"""Etapa `evolve`: un algoritmo de optimización chico cuyo espacio son los greedies (máquinas de
estados constructivas, slot `construction_machine`), con el LLM como operador.

    archivo ← {base}                                   # máquina mínima, una semilla a mano o una generada
    repetir:
        padre    ← torneo en el archivo
        operador ← calendario(padre)                    # add_state | refine_priority(s) | change_transition | simplify
        hijo     ← LLM(padre, operador, diagnóstico por estado del padre, archivo)
        validación liviana (contrato, parámetros extraíbles) + alcance del operador
        fitness  ← tuning corto de sus parámetros en train, media en test
        el hijo entra al archivo si mejora a su nicho (nicho = cantidad de estados)
    al final: las mejores de cada nicho que pasen la validación completa → workspace

Por qué así (el camino de FRG: primero solo movimientos BG, después la prioridad dentro de ese
estado, después un estado de vaciado con vuelta al inicial, y otra vez las prioridades):

- Operadores tipados y con alcance verificado: `add_state` agrega exactamente un estado;
  `refine_priority(s)` cambia la regla de un estado y no las transiciones; `change_transition`
  cambia las transiciones y no las reglas. Cada paso es chico y evaluable.
- Calendario: después de agregar un estado se refina su prioridad (`todo`); si la máquina todavía
  no actúa (todo cae en el comodín), se agrega un estado.
- Tuning dentro del loop: padre e hijo se comparan con sus parámetros afinados (pocas muestras),
  no con los defaults; si no, un estado nuevo con un umbral mal puesto se descartaría aunque la
  estructura sea mejor.
- Etapas incompletas: el estado comodín del framework (`core.machine.FALLBACK`) cubre lo que la
  máquina todavía no sabe hacer; dentro del loop se exige corrección, no calidad mínima.
- Diagnóstico por estado (`core.machine.machine_profile`): pasos y cota perdida por estado; dice
  qué prioridad refinar.
- Archivo con nichos: la mejor máquina de cada cantidad de estados sobrevive aunque sea peor que
  otra más simple, así un paso estructural que al principio empeora puede refinarse después.

Una semilla escrita a mano (`--seed frg_machine`) es conocimiento publicado: queda registrado en
`evolve_stats.json` y las corridas desde la máquina mínima no la ven.
"""

from __future__ import annotations

import ast
import inspect
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from random import Random
from statistics import mean
from typing import Any

from core.validation.base import ValidationReport, fail, ok

from .client import LLMClient, TokenUsage
from .parser import extract_code_blocks
from .prompts import SYSTEM_PROMPT, protocol_source, slot_hint

SLOT = "construction_machine"
OPERATORS = ("add_state", "refine_priority", "change_transition", "simplify")

MINIMAL = '''
COMPONENT = {"name": "minimal", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "requires": [],
             "params": {}}

from core.machine import FALLBACK


class Minimal:
    """Máquina mínima: sin estados propios todavía; cada paso lo decide el comodín del framework."""

    states = ()

    def __init__(self, problem):
        self.problem = problem

    def initial(self, partial):
        return FALLBACK, ()

    def transition(self, partial, state, memory):
        return FALLBACK, ()

    def score(self, partial, state, memory, action):
        return 0.0

    def update(self, partial, state, memory, action):
        return memory


def build_component(problem):
    return Minimal(problem)
'''

OPERATOR_TEXT = {
    "add_state": (
        "Agrega EXACTAMENTE UN estado nuevo, con su regla (score) y las transiciones que entran y salen de él. No cambies "
        "las reglas de los otros estados; toca sus transiciones solo lo necesario para conectar el nuevo. Mira el "
        "diagnóstico: dónde la máquina cae al comodín `{fallback}` o qué estado pierde más cota; un estado nuevo suele "
        "cubrir una situación que hoy nadie maneja bien. Puede ser un estado que vuelva al inicial cuando termina."),
    "refine_priority": (
        "Cambia SOLO la regla (score) del estado `{target}`: a qué candidato le da prioridad y cómo desempata (qué "
        "elemento mover o elegir primero, hacia dónde, con qué criterio secundario). No cambies `transition`, ni los "
        "estados, ni las reglas de los otros estados. Si introduces un número que decide algo, que sea un parámetro."),
    "change_transition": (
        "Cambia SOLO las transiciones (`transition`): cuándo se entra a un estado, cuándo se sale, a cuál se pasa, con "
        "qué memoria se entra. No cambies las reglas (score) ni la lista de estados. Un umbral nuevo va como parámetro."),
    "simplify": (
        "Simplifica: quita un estado, una condición o un parámetro que no aporte (mira el diagnóstico: un estado con "
        "pocos pasos o que no pierde ni gana nada). Tiene que construir igual o mejor, con menos."),
}


@dataclass
class Individual:
    id: int
    name: str
    source: str
    factory: Any
    component: dict
    states: tuple
    parent: int | None = None
    op: str = "base"
    target: str | None = None
    todo: list = field(default_factory=list)  # estados cuya prioridad falta refinar
    params: dict = field(default_factory=dict)  # los afinados en train
    train: float = float("inf")
    fitness: float = float("inf")  # media en test con los parámetros afinados
    profile: dict = field(default_factory=dict)
    rejections: list = field(default_factory=list)  # de sus hijos, para no repetirlos

    @property
    def niche(self) -> int:
        return len(self.states)

    def row(self) -> dict:
        return {"id": self.id, "name": self.name, "parent": self.parent, "op": self.op, "target": self.target,
                "states": list(self.states), "params": self.params, "train": _r(self.train), "fitness": _r(self.fitness)}


def _r(x: float) -> float | None:
    return None if x == float("inf") else round(x, 3)


# ---------------------------------------------------------------- evaluación
class Harness:
    """Construye con la máquina (greedy o beam search) y mide el objetivo; una excepción o una
    solución infactible cuenta como infinito."""

    def __init__(self, pack, mode: str = "greedy", beam_width: int = 3, max_seconds: float = 60.0):
        if mode not in ("greedy", "beam"):
            raise ValueError("mode debe ser greedy o beam")
        self.pack, self.mode, self.beam_width, self.max_seconds = pack, mode, beam_width, max_seconds

    def constructor(self, problem, machine):
        from core.beam_search import BeamSearchConstructor
        from core.construction import GreedyConstructor

        if self.mode == "greedy":
            return GreedyConstructor(problem, machine)
        nb = self.beam_width
        return BeamSearchConstructor(problem, machine, beam_width=nb, branching=2 * nb, max_seconds=self.max_seconds)

    def run(self, factory, params: dict, inst) -> float:
        P = self.pack.problem_factory(inst)
        try:
            sol = self.constructor(P, factory(P, **params)).build(inst, Random(0))
            if not P.is_feasible(sol):
                return float("inf")
            return float(P.objective(sol))
        except Exception:  # noqa: BLE001
            return float("inf")

    def mean(self, factory, params: dict, instances) -> float:
        vals = [self.run(factory, params, inst) for inst in instances]
        return float("inf") if any(v == float("inf") for v in vals) else mean(vals)


def _sample(spec: dict, rng: Random) -> Any:
    t = spec["type"]
    if t == "bool":
        return rng.random() < 0.5
    if t == "cat":
        return rng.choice(list(spec["values"]))
    lo, hi = spec["range"]
    return rng.randint(int(lo), int(hi)) if t == "int" else rng.uniform(float(lo), float(hi))


def tune(harness: Harness, factory, component: dict, train, test, samples: int, rng: Random) -> tuple[dict, float, float]:
    """Tuning corto: los defaults y `samples − 1` puntos al azar del espacio de parámetros del
    componente, en train; el mejor se mide en test. (parámetros, media en train, media en test)."""
    specs = component.get("params") or {}
    defaults = {p: s.get("default") for p, s in specs.items() if "default" in s}
    cands = [defaults] + [{p: _sample(s, rng) for p, s in specs.items()} for _ in range(max(0, samples - 1) if specs else 0)]
    best, best_train = defaults, float("inf")
    for params in cands:
        v = harness.mean(factory, params, train)
        if v < best_train:
            best, best_train = params, v
    return best, best_train, harness.mean(factory, best, test)


def profile(harness: Harness, ind: Individual, instances) -> tuple[dict, str]:
    """Diagnóstico por estado del individuo (con sus parámetros afinados), sumado en `instances`,
    y la traza comprimida de la instancia donde más se pierde."""
    from core.machine import FALLBACK, MachinePolicy, compress_trace, machine_profile, machine_trace

    total: dict[str, dict] = {}
    worst = None
    for inst in instances:
        P = harness.pack.problem_factory(inst)
        view = P.construction_view(inst)
        try:
            prof = machine_profile(MachinePolicy(ind.factory(P, **ind.params), P), view, max_steps=20_000)
        except Exception:  # noqa: BLE001
            continue
        lost = sum(r["lost"] for r in prof.values())
        for st, r in prof.items():
            t = total.setdefault(st, {"steps": 0, "lost": 0.0, "rising": 0})
            for k in t:
                t[k] += r[k]
        if worst is None or lost > worst[0]:
            worst = (lost, inst, P, view)
    trace = ""
    if worst is not None:
        _, inst, P, view = worst
        steps = machine_trace(MachinePolicy(ind.factory(P, **ind.params), P), P.construction_view(inst), max_steps=20_000)
        text = repr(inst)
        trace = f"Instancia donde más pierde:\n```\n{text[:600]}\n```\nTraza (greedy; `estado: acciones`):\n```\n{compress_trace(steps)}\n```"
    ind.profile = total
    return total, trace


def profile_text(prof: dict) -> str:
    from core.machine import FALLBACK

    if not prof:
        return "(sin datos)"
    lines = ["| estado | pasos | cota perdida | pasos que suben la cota |", "|---|---|---|---|"]
    for st, r in sorted(prof.items(), key=lambda kv: -kv[1]["lost"]):
        name = f"{st} (comodín del framework)" if st == FALLBACK else st
        lines.append(f"| {name} | {r['steps']} | {r['lost']:g} | {r['rising']} |")
    return "\n".join(lines)


# ---------------------------------------------------------------- validación liviana y alcance
def light_validation(path: Path, contexts) -> tuple[ValidationReport, Any, dict | None]:
    """Dentro del loop: contrato del slot y parámetros extraíbles, sin calidad mínima ni la sonda
    grande (lo decide el fitness). Lo que sale del loop pasa además la validación completa."""
    from core.validation.contractual import check_slot
    from core.validation.params import constants_check, machine_signature, params_check
    from core.validation.resources import static_cache_check
    from core.validation.syntactic import check_component_dict, check_protocol, load_module

    report = ValidationReport(subject=path.name)
    module, r = load_module(path)
    report.add(r)
    if module is None:
        return report, None, None
    component, factory = getattr(module, "COMPONENT", None), getattr(module, "build_component", None)
    if not isinstance(component, dict) or not callable(factory):
        report.add(fail("syntactic", "component_present", "el módulo debe definir COMPONENT y build_component(problem, **params)"))
        return report, module, component
    if component.get("slot") != SLOT:
        report.add(fail("syntactic", "same_slot", f"el slot debe ser {SLOT}"))
        return report, module, component
    report.add(static_cache_check(module, "componente"))
    report.add(constants_check(module))
    if not report.passed:
        return report, module, component
    for ctx in contexts:
        try:
            impl = factory(ctx.problem)
        except Exception as exc:  # noqa: BLE001
            report.add(fail("syntactic", "factory_runs", f"build_component(problem) lanzó {type(exc).__name__}: {exc}"))
            return report, module, component
        _, results = check_component_dict(component, impl)
        report.extend(results)
        report.add(check_protocol(SLOT, impl))
        if report.passed:
            report.extend(check_slot(SLOT, impl, ctx))
        if not report.passed:
            return report, module, component
    where = [(ctx.instances[0], ctx.problem) for ctx in contexts if ctx.instances]
    try:
        report.extend(params_check(component, factory, where, machine_signature))
    except Exception as exc:  # noqa: BLE001
        report.add(fail("syntactic", "params_accepted", f"construir con otros valores de los parámetros lanzó {type(exc).__name__}: {exc}"))
    return report, module, component


def _method_dump(source: str, name: str) -> str | None:
    """El AST (sin posiciones) del método `name` de la clase que declara `states`."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ClassDef) and any(isinstance(b, ast.Assign) and any(getattr(t, "id", None) == "states" for t in b.targets)
                                                  for b in node.body):
            for b in node.body:
                if isinstance(b, ast.FunctionDef) and b.name == name:
                    return ast.dump(b, include_attributes=False)
    return None


def scope_check(op: str, target: str | None, parent: Individual, child_states: tuple, child_source: str) -> str | None:
    """None si el hijo respeta el alcance del operador; si no, por qué."""
    ps, cs = tuple(parent.states), tuple(child_states)
    if op == "add_state":
        if len(cs) != len(ps) + 1 or not set(ps) <= set(cs):
            return f"add_state debe agregar exactamente un estado a {list(ps)} (el hijo tiene {list(cs)})"
    elif op == "refine_priority":
        if cs != ps:
            return f"refine_priority no cambia los estados ({list(ps)}; el hijo tiene {list(cs)})"
        if _method_dump(parent.source, "transition") != _method_dump(child_source, "transition"):
            return f"refine_priority({target}) cambia solo score; el hijo modificó transition"
    elif op == "change_transition":
        if cs != ps:
            return f"change_transition no cambia los estados ({list(ps)}; el hijo tiene {list(cs)})"
        if _method_dump(parent.source, "score") != _method_dump(child_source, "score"):
            return "change_transition cambia solo transition; el hijo modificó score"
    elif op == "simplify":
        if len(cs) > len(ps):
            return f"simplify no agrega estados ({list(ps)}; el hijo tiene {list(cs)})"
    return None


# ---------------------------------------------------------------- operadores y selección
def schedule(parent: Individual, rng: Random) -> tuple[str, str | None]:
    """El operador para un hijo de `parent`: si la máquina todavía no actúa (todo en el comodín),
    agregar un estado; si tiene estados recién agregados, refinar su prioridad; si no, al azar."""
    from core.machine import FALLBACK

    own = {k: v["steps"] for k, v in parent.profile.items() if k != FALLBACK}
    if not any(own.values()):
        return "add_state", None
    if parent.todo:
        return "refine_priority", parent.todo[0]
    ops = [("add_state", 0.35), ("refine_priority", 0.35), ("change_transition", 0.2)]
    if len(parent.states) > 1:
        ops.append(("simplify", 0.1))
    r, acc = rng.random() * sum(w for _, w in ops), 0.0
    for op, w in ops:
        acc += w
        if r <= acc:
            break
    target = None
    if op == "refine_priority":  # el estado propio que más cota pierde
        cands = sorted(own, key=lambda s: -parent.profile[s]["lost"]) or list(parent.states)
        target = cands[0]
    return op, target


def tournament(archive: list[Individual], rng: Random) -> Individual:
    if len(archive) == 1:
        return archive[0]
    a, b = rng.sample(archive, 2)
    return a if a.fitness <= b.fitness else b


def admit(archive: list[Individual], child: Individual, size: int) -> bool:
    """El hijo entra si su nicho (cantidad de estados) está vacío o si mejora al peor del nicho; el
    archivo se recorta a `size` sacando al peor de los nichos con más de un individuo (o al peor)."""
    if child.fitness == float("inf"):
        return False
    same = [x for x in archive if x.niche == child.niche]
    if same and len(same) >= 2 and child.fitness >= max(x.fitness for x in same):
        return False
    if same and len(same) == 1 and child.fitness >= same[0].fitness and len(archive) >= size:
        return False
    archive.append(child)
    while len(archive) > size:
        crowded = [x for x in archive if sum(y.niche == x.niche for y in archive) > 1] or archive
        archive.remove(max(crowded, key=lambda x: x.fitness))
    return child in archive


def archive_text(archive: list[Individual]) -> str:
    rows = ["| máquina | estados | fitness (test) | viene de |", "|---|---|---|---|"]
    for x in sorted(archive, key=lambda x: x.fitness):
        rows.append(f"| {x.name} | {', '.join(x.states)} | {x.fitness:.2f} | {x.op}{'(' + x.target + ')' if x.target else ''} |")
    return "\n".join(rows)


def evolve_prompt(spec, parent: Individual, op: str, target: str | None, prof: str, trace: str, archive: list[Individual],
                  seed: bool) -> str:
    from core.machine import FALLBACK

    who = (" La base es una heurística publicada escrita a mano; devuelve un módulo nuevo con solo tu versión (puedes "
           "importar funciones de los mismos módulos)." if seed and parent.op == "base" else "")
    parts = [
        f"# Tarea\nEstás mejorando paso a paso un constructor greedy del problema **{spec.name}**, escrito como máquina de "
        f"estados (slot `{SLOT}`). En cada paso se aplica UN operador a una máquina del archivo; el resultado se afina "
        f"(sus parámetros) y se compara en instancias que no ves.{who}",
        f"\n# Operador de este paso: `{op}`\n" + OPERATOR_TEXT[op].format(target=target, fallback=FALLBACK),
        f"\nLa máquina puede devolver `FALLBACK` (`from core.machine import FALLBACK`, el estado \"{FALLBACK}\") desde "
        "`transition` cuando ninguno de sus estados sabe qué hacer: el framework elige entonces la acción que menos sube la "
        "cota inferior de la vista. No va en `states`.",
        f"\n# Máquina padre: `{parent.name}` (fitness {parent.fitness:.2f}, parámetros afinados {parent.params})\n"
        f"```python\n{parent.source}\n```",
        f"\n# Diagnóstico del padre por estado (instancias de entrenamiento)\n{prof}\n\n{trace}",
        f"\n# Archivo (menor fitness = mejor)\n{archive_text(archive)}",
        f"\n# Contrato del slot\n```python\n{protocol_source(SLOT)}```",
        "\n# Reglas\n" + slot_hint(spec, SLOT),
        f"\n# Problema\n{spec.description}",
    ]
    if spec.construction_source:
        parts.append(f"\n## Vista constructiva: el estado parcial y la acción\n```python\n{spec.construction_source}\n```")
    if parent.rejections:
        parts.append("\n# Hijos de esta máquina ya rechazados (no los repitas)\n" + "\n".join(f"- {r}" for r in parent.rejections[-4:]))
    parts.append("\nPon un nombre descriptivo nuevo en COMPONENT[\"name\"]. Devuelve UN solo bloque ```python``` con el módulo "
                 "completo (COMPONENT y build_component(problem, **params)).")
    return "\n".join(parts)


# ---------------------------------------------------------------- bases
def _module_individual(source: str, path: Path, id_: int, problem) -> Individual:
    from core.validation.syntactic import load_module

    path.write_text(source)
    module, r = load_module(path)
    if module is None:
        raise SystemExit(f"no se pudo cargar la base {path}: {r.message}")
    comp = module.COMPONENT
    return Individual(id_, comp["name"], source, module.build_component, comp, tuple(module.build_component(problem).states))


def base_individual(pack, workspace: Path, seed: str | None, base: str | None) -> tuple[Individual, bool]:
    """(individuo base, ¿es una semilla a mano?). Por defecto, la máquina mínima."""
    tmp = workspace / SLOT / "_evolve"
    tmp.mkdir(parents=True, exist_ok=True)
    inst = pack.make_instances(1, 0, pack.parse_size(pack.micro_size or pack.default_size))[0]
    problem = pack.problem_factory(inst)
    if seed:
        for component, factory in pack.handwritten:
            if component["name"] == seed and component["slot"] == SLOT:
                obj = factory(problem)
                module = inspect.getmodule(type(obj))
                src = re.sub(r"^from \.(\w*) import",
                             lambda m: f"from {module.__package__}{'.' + m.group(1) if m.group(1) else ''} import",
                             inspect.getsource(module), flags=re.M)
                ind = Individual(0, seed, src, factory, dict(component), tuple(obj.states))
                return ind, True
        raise SystemExit(f"el pack {pack.name} no tiene una máquina a mano {seed}")
    if base:
        paths = sorted((workspace / SLOT).glob(f"{base}_r*.py"), key=lambda p: int(p.stem.rpartition("_r")[2] or 0))
        if not paths:
            raise SystemExit(f"no hay {SLOT}/{base}_r*.py en {workspace}")
        return _module_individual(paths[-1].read_text(), tmp / "base.py", 0, problem), False
    return _module_individual(MINIMAL, tmp / "minimal.py", 0, problem), False


# ---------------------------------------------------------------- bucle
@dataclass
class EvolveResult:
    individuals: list[dict] = field(default_factory=list)  # todos los intentos (árbol)
    archive: list[str] = field(default_factory=list)
    written: list[dict] = field(default_factory=list)  # los que pasaron la validación completa
    seed: bool = False
    rounds: int = 0

    def as_dict(self) -> dict:
        return {"seed": self.seed, "rounds": self.rounds, "archive": self.archive, "written": self.written,
                "individuals": self.individuals}


def evolve(client: LLMClient, pack, spec, workspace: str | Path, harness: Harness, rounds: int = 12, archive_size: int = 4,
           tune_samples: int = 6, n_train: int = 4, n_test: int = 8, size: str | None = None, seed: str | None = None,
           base: str | None = None, rng_seed: int = 0, tokens: TokenUsage | None = None, deadline: float | None = None,
           verbose: bool = True) -> EvolveResult:
    from .generator import validate_generated_module

    ws = Path(workspace)
    tokens = tokens if tokens is not None else TokenUsage()
    rng = Random(rng_seed)
    sz = pack.parse_size(size or pack.default_size)
    train = pack.make_instances(n_train, 9100, sz)
    test = pack.make_instances(n_test, 10100, sz)
    contexts = [c for c in pack.make_contexts(strict=False)]
    root, is_seed = base_individual(pack, ws, seed, base)
    res = EvolveResult(seed=is_seed)
    root.params, root.train, root.fitness = tune(harness, root.factory, root.component, train, test, tune_samples, rng)
    profile(harness, root, train)
    archive, everyone = [root], [root]
    res.individuals.append({**root.row(), "status": "base"})
    tmp = ws / SLOT / "_evolve"
    last = 0.0
    for rnd in range(1, rounds + 1):
        if rnd > 1 and deadline is not None and deadline - time.monotonic() < last:
            res.individuals.append({"round": rnd, "status": "sin tiempo"})
            break
        t0 = time.monotonic()
        res.rounds = rnd
        parent = tournament(archive, rng)
        op, target = schedule(parent, rng)
        prof, trace = profile(harness, parent, train)
        text = client.complete(SYSTEM_PROMPT, evolve_prompt(spec, parent, op, target, profile_text(prof), trace, archive, is_seed))
        used = getattr(client, "last_usage", None)
        if isinstance(used, TokenUsage):
            tokens.add(used)
        cid = len(everyone)
        entry = {"id": cid, "parent": parent.id, "op": op, "target": target, "round": rnd}
        blocks = extract_code_blocks(text)
        if not blocks:
            parent.rejections.append(f"{op}: la respuesta no traía un bloque ```python```")
            res.individuals.append({**entry, "status": "sin código"})
            continue
        path = tmp / f"cand_{cid}.py"
        path.write_text(blocks[0])
        report, module, component = light_validation(path, contexts)
        reason = None if report.passed else report.feedback()[:700]
        states = ()
        if reason is None:
            states = tuple(module.build_component(contexts[0].problem).states)
            reason = scope_check(op, target, parent, states, blocks[0])
        if reason is not None:
            parent.rejections.append(f"{op}{'(' + target + ')' if target else ''}: {reason}")
            res.individuals.append({**entry, "status": "rechazado", "reason": reason})
            last = time.monotonic() - t0
            if verbose:
                print(f"[evolve] ronda {rnd}: {op} sobre {parent.name} ✘ {reason[:160]}")
            continue
        name = component.get("name") or f"machine_{cid}"
        if any(x.name == name for x in everyone):
            name = f"{name}_{cid}"
            component = dict(component, name=name)
        child = Individual(cid, name, blocks[0], module.build_component, component, states, parent=parent.id, op=op, target=target)
        new_states = [s for s in states if s not in parent.states]
        child.todo = new_states if op == "add_state" else [s for s in parent.todo if s != target and s in states]
        child.params, child.train, child.fitness = tune(harness, child.factory, component, train, test, tune_samples, rng)
        profile(harness, child, train)
        everyone.append(child)
        admitted = admit(archive, child, archive_size)
        res.individuals.append({**child.row(), "round": rnd, "status": "archivo" if admitted else "no mejora su nicho"})
        if not admitted:
            parent.rejections.append(f"{op}{'(' + target + ')' if target else ''}: `{name}` ({', '.join(states)}) dio fitness "
                                     f"{child.fitness:.2f}; no mejora a las máquinas de {child.niche} estados del archivo")
        last = time.monotonic() - t0
        if verbose:
            print(f"[evolve] ronda {rnd}: {op}{'(' + target + ')' if target else ''} sobre {parent.name} → {name} "
                  f"({', '.join(states)}) fitness {child.fitness:.2f} {'✔' if admitted else '·'}")
    # salida: el mejor de cada nicho que pase la validación completa (la del catálogo)
    res.archive = [x.name for x in sorted(archive, key=lambda x: x.fitness)]
    out_dir = ws / SLOT
    for x in sorted(archive, key=lambda x: x.fitness):
        if x.op == "base":
            continue
        path = out_dir / f"{x.name}_r1.py"
        path.write_text(x.source)
        report, _, _ = validate_generated_module(path, contexts)
        if report.passed:
            res.written.append({"name": x.name, "path": str(path), "fitness": _r(x.fitness), "params": x.params})
        else:
            path.unlink()
            res.written.append({"name": x.name, "fitness": _r(x.fitness), "rejected": report.feedback()[:400]})
    return res


def save_stats(workspace: str | Path, res: EvolveResult, tokens: TokenUsage, model: str = "") -> Path:
    path = Path(workspace) / "evolve_stats.json"
    runs = json.loads(path.read_text()) if path.exists() else []
    runs.append({**res.as_dict(), "tokens": tokens.as_dict(model)})
    path.write_text(json.dumps(runs, indent=2, ensure_ascii=False, default=str))
    return path


def main(pack, argv: list[str] | None = None, workspace: str | None = None, spec=None) -> EvolveResult:
    import argparse

    ap = argparse.ArgumentParser(description="Evolucionar máquinas de estados constructivas (etapa evolve)")
    ap.add_argument("--seed", default=None, help="partir de una máquina escrita a mano del pack (p.ej. frg_machine)")
    ap.add_argument("--base", default=None, help="partir de una máquina generada del workspace")
    ap.add_argument("--rounds", type=int, default=12)
    ap.add_argument("--archive", type=int, default=4)
    ap.add_argument("--tune-samples", type=int, default=6)
    ap.add_argument("--mode", choices=["greedy", "beam"], default="greedy")
    ap.add_argument("--beam-width", type=int, default=3)
    ap.add_argument("--train", type=int, default=4)
    ap.add_argument("--test", type=int, default=8)
    ap.add_argument("--size", default=None)
    ap.add_argument("--rng-seed", type=int, default=0)
    ap.add_argument("--workspace", default=workspace or pack.default_workspace)
    ap.add_argument("--max-minutes", type=float, default=35.0)
    ap.add_argument("--provider", choices=["openai", "anthropic"], default="openai")
    ap.add_argument("--model", default=None)
    args = ap.parse_args(argv)
    if args.seed and args.base:
        raise SystemExit("--seed y --base son excluyentes")
    from .client import TranscriptClient

    if args.provider == "anthropic":
        from .client import AnthropicClient as Client
    else:
        from .client import OpenAIClient as Client
    inner = Client(model=args.model) if args.model else Client()
    client = TranscriptClient(inner, Path(args.workspace) / "transcript_evolve")
    tokens = TokenUsage()
    res = evolve(client, pack, spec or pack.make_spec(), args.workspace, Harness(pack, args.mode, args.beam_width),
                 rounds=args.rounds, archive_size=args.archive, tune_samples=args.tune_samples, n_train=args.train,
                 n_test=args.test, size=args.size, seed=args.seed, base=args.base, rng_seed=args.rng_seed, tokens=tokens,
                 deadline=time.monotonic() + 60 * args.max_minutes)
    print(json.dumps({k: v for k, v in res.as_dict().items() if k != "individuals"}, indent=2, ensure_ascii=False, default=str))
    save_stats(args.workspace, res, tokens, getattr(inner, "model", ""))
    return res


def _module_main(argv: list[str] | None = None) -> None:
    """`python -m llm.evolve --problem cpmp [--seed frg_machine] ...`: con el pack de referencia del
    problema (sobre un modelo generado: `python -m llm.cycle evolve`)."""
    import sys

    argv = list(sys.argv[1:] if argv is None else argv)
    if "--problem" not in argv:
        raise SystemExit("falta --problem (clsp, cvrp o cpmp)")
    k = argv.index("--problem")
    problem = argv[k + 1]
    del argv[k:k + 2]
    from .cycle import base_pack

    pack = base_pack(problem)
    main(pack, argv, workspace=f"generated/{pack.name}_evolve")


__all__ = ["evolve", "Harness", "Individual", "EvolveResult", "tune", "schedule", "admit", "scope_check", "light_validation",
           "evolve_prompt", "MINIMAL", "OPERATORS", "main"]


if __name__ == "__main__":
    _module_main()
