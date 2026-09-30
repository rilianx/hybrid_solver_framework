"""Etapa `evolve`: un algoritmo de optimización chico cuyo espacio son los greedies (máquinas de
estados constructivas, slot `construction_machine`), con el LLM como operador.

    archivo ← {base}                                   # máquina mínima, una semilla a mano o una generada
    repetir:
        padre    ← torneo en el archivo
        operador ← calendario(padre)                    # add_simple | add_macro | refine_rule(r) | change_priority | simplify
        hijo     ← LLM(padre, operador, diagnóstico por estado del padre, archivo)
        validación liviana (contrato, parámetros extraíbles) + alcance del operador
        fitness  ← tuning corto de sus parámetros en train, media en test
        el hijo entra al archivo si mejora a su nicho (nicho = cantidad de estados)
    al final: las mejores de cada nicho que pasen la validación completa → workspace

Por qué así (el camino de FRG: primero solo movimientos BG, después la prioridad dentro de ese
estado, después un estado de vaciado con vuelta al inicial, y otra vez las prioridades):

- Máquinas de reglas (`core.rules.RuleMachine`): reglas simples (se reevalúan en cada paso) y
  macros (un compromiso de varios pasos: `start` fija su parámetro, `done` dice cuándo termina),
  cada una con una prioridad; el controlador es fijo.
- Operadores tipados y con alcance verificado clase por clase: `add_simple` agrega una regla
  simple; `add_macro`, una macro (el paso que hace falta para llegar a FRG: "sacar de una pila"
  sola no sirve, sirve comprometida con la misma pila); `refine_rule(r)` cambia solo la clase de
  la regla r; `change_priority` cambia solo prioridades. Cada paso es chico y evaluable.
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
from core.validation.params import llm_view

from .client import LLMClient, TokenUsage
from .parser import extract_code_blocks
from .prompts import SYSTEM_PROMPT, protocol_source, slot_hint

SLOT = "construction_machine"
OPERATORS = ("add_simple", "add_macro", "refine_rule", "change_priority", "simplify")
ADDS = ("add_simple", "add_macro")
MACRO_TRIES = 3  # una macro nueva suele nacer mala (corrida 76: 92,4 y 97,2): más refinamientos antes de soltarla

MINIMAL = '''
COMPONENT = {"name": "minimal", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "requires": [],
             "params": {}}

from core.rules import RuleMachine


def build_component(problem):
    """Máquina mínima: sin reglas todavía; cada paso lo decide el comodín del framework."""
    return RuleMachine(problem, [])
'''

OPERATOR_TEXT = {
    "add_simple": (
        "Agrega EXACTAMENTE UNA regla SIMPLE nueva: una clase con `name`, `priority` y `allowed(parcial, memoria, "
        "candidatos)` (el subconjunto de los candidatos que considera, en orden de preferencia; [] = no aplica), y si "
        "hace falta `score(parcial, memoria, acción)` (menor = mejor). Sin `start` ni `done`: se reevalúa en cada paso. "
        "Elige su prioridad respecto de las que ya hay (mayor = se prefiere; la primera, 100). No cambies las otras "
        "reglas. Mira el diagnóstico: dónde la máquina cae al comodín `{fallback}` y qué hace el óptimo que ninguna regla "
        "permite. Una regla buena permite UN tipo de movimiento: en vez de un puntaje compuesto que ordena todos los candidatos, "
        "prefiere varias reglas con prioridades."),
    "add_macro": (
        "Agrega EXACTAMENTE UNA MACRO nueva: un compromiso de varios pasos. Es una regla con `name`, `priority`, "
        "`start(parcial, memoria) -> memoria` (al activarse fija su parámetro, p.ej. qué objetivo atender, y lo guarda en "
        "la memoria), `allowed(parcial, memoria, candidatos)` (solo las acciones de ese compromiso, en orden), `done("
        "parcial, memoria) -> bool` (cuándo terminó) y, si hace falta, `init`, `update` y `score`. Mientras no termine, "
        "el controlador la sigue aunque otra regla tenga más prioridad. Elige su prioridad respecto de las que hay (p.ej. "
        "50 si solo debe activarse cuando las demás no aplican). No cambies las otras reglas. Mira los tramos óptimos del "
        "diagnóstico: una secuencia de pasos óptimos que atienden el mismo objetivo es una macro."),
    "refine_rule": (
        "Cambia SOLO la regla `{target}` (su clase, sin su `priority`): qué permite, en qué orden, cuándo no aplica, qué "
        "recuerda, qué fija en `start`, cuándo termina. No cambies las otras reglas ni las prioridades. Mira su precisión "
        "y los contraejemplos donde ella decidió: qué haría el óptimo y si estaba entre lo que permitió (si no estaba, "
        "el problema es el set; si estaba, el orden)."),
    "change_priority": (
        "Cambia SOLO las prioridades (`priority`) de las reglas, sin tocar nada más. Mira la cobertura y la precisión "
        "de cada regla: una regla precisa que casi no se elige necesita más prioridad; una imprecisa que se elige mucho, "
        "menos."),
    "simplify": (
        "Simplifica: quita una regla o una condición que no aporte (una regla que casi nunca se elige o que no pierde ni "
        "gana nada). Tiene que construir igual o mejor, con menos."),
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
    self_sorted: dict = field(default_factory=dict)  # por tamaño: [instancias que completa sola, total]
    regret: dict = field(default_factory=dict)  # con oráculo: estado → {steps, regret, wrong} (exacto)
    examples: list = field(default_factory=list)  # con oráculo: los peores pasos, con lo que haría el óptimo
    good: list = field(default_factory=list)  # con oráculo: pasos donde acertó (para no romperlos)
    rejections: list = field(default_factory=list)  # de sus hijos, para no repetirlos
    refine_failures: dict = field(default_factory=dict)  # regla → hijos fallidos de refine_rule
    rules: dict = field(default_factory=dict)  # con oráculo: regla → {applies, optimal, chosen} (cobertura y precisión)
    breadth: dict = field(default_factory=dict)  # regla → {applies, all}: en cuántos pasos permite TODOS los candidatos

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
        """Objetivo; una solución infactible cuenta como 2·objetivo + 1 (una penalización finita: con
        tamaños mezclados, una máquina que falla en alguna instancia grande sigue siendo comparable y
        refinable), una excepción como infinito."""
        P = self.pack.problem_factory(inst)
        try:
            sol = self.constructor(P, factory(P, **params)).build(inst, Random(0))
            obj = float(P.objective(sol))
            return obj if P.is_feasible(sol) else 2.0 * obj + 1.0
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


ORACLE_INSTANCES = 2  # el oráculo exacto cuesta: ≈ 50 s por máquina nueva en 2 instancias de 5×5 (después, caché)


def profile(harness: Harness, ind: Individual, instances, oracle_instances: int | None = None) -> tuple[dict, str]:
    """Diagnóstico por estado del individuo (con sus parámetros afinados), sumado en `instances`,
    y la traza comprimida de la instancia donde más se pierde."""
    from core.machine import FALLBACK, MachinePolicy, compress_trace, machine_profile, machine_trace

    total: dict[str, dict] = {}
    worst = None
    ind.self_sorted = {}
    for inst in instances:
        P = harness.pack.problem_factory(inst)
        view = P.construction_view(inst)
        try:
            prof, alone = machine_profile(MachinePolicy(ind.factory(P, **ind.params), P), view, max_steps=20_000, with_end=True)
        except Exception:  # noqa: BLE001
            continue
        key = getattr(inst, "name", "") or "instancias"
        done = ind.self_sorted.setdefault(key, [0, 0])
        done[0] += alone
        done[1] += 1
        lost = sum(r["lost"] for r in prof.values())
        for st, r in prof.items():
            t = total.setdefault(st, {"steps": 0, "lost": 0.0, "rising": 0})
            for k in t:
                t[k] += r[k]
        if worst is None or lost > worst[0]:
            worst = (lost, inst, P, view)
    oracle = getattr(harness.pack, "oracle_distance", None)
    ind.regret, ind.examples, ind.good = {}, [], []
    if callable(oracle):  # arrepentimiento exacto por estado y contraejemplos, donde el oráculo alcanza
        from core.machine import machine_regret

        budget = ORACLE_INSTANCES if oracle_instances is None else oracle_instances
        used = 0
        for inst in sorted(instances, key=lambda i: getattr(i, "N", 0)):  # las más chicas primero: donde alcanza
            if used >= budget:
                break
            P = harness.pack.problem_factory(inst)
            try:
                r = machine_regret(MachinePolicy(ind.factory(P, **ind.params), P), P.construction_view(inst),
                                   lambda p, inst=inst: oracle(inst, p), continuation=8)  # tramos largos: dejan ver una macro
            except Exception:  # noqa: BLE001
                r = None
            if r is None:
                continue
            used += 1
            for st, row in r["by_state"].items():
                t = ind.regret.setdefault(st, {"steps": 0, "regret": 0, "wrong": 0})
                for k in t:
                    t[k] += row[k]
            label = f"{getattr(inst, 'name', '') or 'instancia'} #{used}"
            ind.examples += [dict(e, instance=label) for e in r["examples"]]
            ind.good += [dict(e, instance=label) for e in r["good"]]
        from core.machine import _diverse
        from core.rules import rule_quality

        ind.rules = {}
        for inst in [i for i in sorted(instances, key=lambda i: getattr(i, "N", 0))][:budget]:
            P = harness.pack.problem_factory(inst)
            try:
                q = rule_quality(MachinePolicy(ind.factory(P, **ind.params), P), P.construction_view(inst),
                                 lambda p, inst=inst: oracle(inst, p))
            except Exception:  # noqa: BLE001
                q = None
            if q is None:
                continue
            for n, row in q["rules"].items():
                t = ind.rules.setdefault(n, {"applies": 0, "optimal": 0, "chosen": 0, "steps": 0})
                for k in ("applies", "optimal", "chosen"):
                    t[k] += row[k]
                t["steps"] += q["steps"]

        # variados: primero uno por (estado, instancia), después por gravedad (no los 4 peores de un mismo caso)
        ind.examples = _diverse(sorted(ind.examples, key=lambda e: -e["regret"]), 4, key=lambda e: (e["state"], e["instance"]))
        ind.good = _diverse(ind.good, 2, key=lambda e: e["state"])
    trace = ""
    if worst is not None:
        _, inst, P, view = worst
        steps = machine_trace(MachinePolicy(ind.factory(P, **ind.params), P), P.construction_view(inst), max_steps=20_000)
        text = repr(inst)
        trace = f"Instancia donde más pierde:\n```\n{text[:600]}\n```\nTraza (greedy; `estado: acciones`):\n```\n{compress_trace(steps)}\n```"
    ind.profile = total
    from core.rules import rule_breadth

    ind.breadth = {}
    for inst in instances:
        P = harness.pack.problem_factory(inst)
        try:
            b = rule_breadth(MachinePolicy(ind.factory(P, **ind.params), P), P.construction_view(inst))
        except Exception:  # noqa: BLE001
            b = None
        for n, row in (b or {}).items():
            t = ind.breadth.setdefault(n, {"applies": 0, "all": 0, "share": 0.0, "shadowed_by": {}})
            for k in ("applies", "all", "share"):
                t[k] += row[k]
            for m, c in row["shadowed_by"].items():
                t["shadowed_by"][m] = t["shadowed_by"].get(m, 0) + c
    return total, trace


BROAD = 0.5  # una regla que permite todos los candidatos en más de esta fracción de sus pasos es un puntaje compuesto


def broad_rules(ind: Individual) -> list[str]:
    """Las reglas que casi siempre permiten todo, de la más a la menos."""
    rows = [(r["all"] / r["applies"], n) for n, r in ind.breadth.items() if r["applies"] and r["all"] / r["applies"] > BROAD]
    return [n for _, n in sorted(rows, reverse=True)]


SHADOWED = 0.2  # una regla tapada en más de esta fracción de los pasos donde aplica se informa


def shadowed(ind: Individual) -> list[tuple[str, str, int, int]]:
    """(regla tapada, la que decidió, pasos, pasos donde la tapada aplica), de la más tapada."""
    out = []
    for n, r in ind.breadth.items():
        for m, c in (r.get("shadowed_by") or {}).items():
            if r["applies"] and c >= 3 and c / r["applies"] > SHADOWED:
                out.append((n, m, c, r["applies"]))
    return sorted(out, key=lambda t: -t[2] / t[3])


def breadth_text(ind: Individual) -> str:
    lines = []
    if ind.breadth:
        rows = [f"`{n}` permite en promedio el {r['share'] / r['applies']:.0%} de los candidatos"
                for n, r in ind.breadth.items() if r["applies"]]
        if rows:
            lines.append("\n\nQué tan ancha es cada regla (cuando aplica): " + "; ".join(rows) + ".")
    broad = broad_rules(ind)
    if broad:
        rows = ", ".join(f"`{n}` en {ind.breadth[n]['all']} de {ind.breadth[n]['applies']} pasos" for n in broad)
        lines.append("Reglas que permiten TODOS los candidatos casi siempre (un puntaje compuesto disfrazado de regla): "
                     f"{rows}. Mejor varias reglas, cada una un tipo de movimiento, con prioridades entre ellas: así cada "
                     "una se puede refinar sola y lo que ninguna sabe hacer lo cubre el comodín.")
    shadow = shadowed(ind)
    if shadow:
        def width(n):
            r = ind.breadth.get(n) or {}
            return r["share"] / r["applies"] if r.get("applies") else 0.0

        rows = []
        for n, m, c, a in shadow:
            row = f"`{n}` aplicaba en {c} de sus {a} pasos donde decidió `{m}`"
            if width(m) > width(n):
                row += f" (`{m}` es la ancha: angostarla le deja esos pasos a `{n}`)"
            else:
                row += (f" (`{n}` es la ancha: angostada a su tipo de movimiento podría ir sobre `{m}` sin taparla)")
            rows.append(row)
        lines.append("Reglas tapadas por otra: " + "; ".join(rows) + ". Mejor angostar la regla ancha que invertir "
                     "prioridades: en FRG la de mayor prioridad (llenar) es estrecha, y cuando no aplica entra la macro de "
                     "reducción.")
    return "\n".join(lines)


def regret_text(ind: Individual) -> str:
    """El arrepentimiento exacto por estado (movimientos de más respecto del óptimo, que el oráculo
    calcula donde alcanza) y los peores pasos con lo que el óptimo sí habría hecho."""
    from core.machine import FALLBACK

    if not ind.regret:
        return ""
    lines = ["\n\n# Contra el óptimo (oráculo exacto, en las instancias donde alcanza)",
             "Movimientos de más que causa cada estado (su suma es movimientos − óptimo):",
             "| estado | pasos | movimientos de más | pasos que se apartan del óptimo |", "|---|---|---|---|"]
    for st, r in sorted(ind.regret.items(), key=lambda kv: -kv[1]["regret"]):
        name = f"{st} (comodín del framework)" if st == FALLBACK else st
        lines.append(f"| {name} | {r['steps']} | {r['regret']} | {r['wrong']} |")
    if ind.rules:
        lines.append("\nCalidad de cada regla: cobertura = en cuántos pasos permite algo; precisión = cuando permite, qué "
                     "fracción de las veces su primera acción es óptima; elegida = cuántas veces decidió. Precisa y poco "
                     "elegida: problema de prioridad; imprecisa: problema de la regla.")
        lines.append("| regla | cobertura | precisión | elegida |")
        lines.append("|---|---|---|---|")
        for n, r in ind.rules.items():
            prec = f"{r['optimal']}/{r['applies']} ({r['optimal'] / r['applies']:.0%})" if r["applies"] else "—"
            lines.append(f"| {n} | {r['applies']}/{r['steps']} | {prec} | {r['chosen']} |")
    if ind.examples:
        lines.append("\nPasos donde la máquina se aparta del óptimo (contraejemplos: busca la regla simple que los evite). "
                     "Los puntajes son los que les dio TU score (menor = preferida): muestran qué término hizo ganar a la mala.")
        for e in ind.examples:
            opt = ", ".join(f"{a!r} (puntaje {sc:.4g})" for a, sc in zip(e["optimal"][:4], e.get("optimal_scores", [])[:4])) \
                or "(ninguna)"
            cont = ", ".join(repr(a) for a in e.get("continuation", []))
            lines.append(f"- {e['instance']}, estado `{e['state']}`, parcial `{_short(e['partial'])}`:\n"
                         f"  eligió {e['chosen']!r} (puntaje {e.get('chosen_score', float('nan')):.4g}), que cuesta "
                         f"{e['regret']} movimiento(s) de más;\n  el óptimo haría {opt}"
                         + (f";\n  un tramo óptimo desde aquí (varios pasos que atienden el mismo objetivo son una macro): {cont}"
                            if cont else ""))
    if ind.good:
        lines.append("\nPasos donde SÍ eligió como el óptimo (no los rompas al corregir):")
        for e in ind.good:
            lines.append(f"- {e['instance']}, estado `{e['state']}`, parcial `{_short(e['partial'])}`: eligió {e['chosen']!r}")
    return "\n".join(lines)


def _short(obj, n: int = 160) -> str:
    state = getattr(obj, "state", None)
    text = repr(state() if callable(state) else obj)
    return text if len(text) <= n else text[:n] + "…"


def self_sorted_text(ind: Individual) -> str:
    """Cuántas instancias completa la máquina sola, por tamaño: si llega a un parcial sin candidatos
    (el tope de movimientos de la vista, un callejón), el resto lo decide el respaldo de la vista."""
    if not ind.self_sorted:
        return ""
    parts = [f"{k}: {a} de {n}" for k, (a, n) in sorted(ind.self_sorted.items())]
    warn = any(a < n for a, n in ind.self_sorted.values())
    return ("\n\nCompleta sola (sin el respaldo de la vista): " + ", ".join(parts)
            + (". Donde no, se queda sin candidatos (agota el tope de movimientos o llega a un callejón) y la solución "
               "la arma el respaldo: eso es lo primero que hay que corregir." if warn else "."))


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
def light_validation(path: Path, contexts, reach=None) -> tuple[ValidationReport, Any, dict | None]:
    """Dentro del loop: contrato del slot y parámetros extraíbles, sin calidad mínima ni la sonda
    grande (lo decide el fitness). Lo que sale del loop pasa además la validación completa.

    `reach`: [(instancia, problema)] de entrenamiento. Un estado que no se alcanza en las
    micro-instancias pero sí en esas no es código muerto: es un estado para instancias más
    grandes (corrida 68: 5 de 12 rondas perdidas por un `finish` o un `drain` que solo se activan
    con más contenedores)."""
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
    reach_pending = False
    for ctx in contexts:
        try:
            impl = factory(ctx.problem)
        except Exception as exc:  # noqa: BLE001
            report.add(fail("syntactic", "factory_runs", f"build_component(problem) lanzó {type(exc).__name__}: {exc}"))
            return report, module, component
        from core.rules import RuleMachine

        if not isinstance(impl, RuleMachine):
            report.add(fail("syntactic", "rule_machine", "build_component debe devolver una `core.rules.RuleMachine(problem, "
                                                         "[reglas...])`: reglas simples y macros, cada una con `priority`"))
            return report, module, component
        _, results = check_component_dict(component, impl)
        report.extend(results)
        report.add(check_protocol(SLOT, impl))
        if report.passed:
            slot_results = check_slot(SLOT, impl, ctx)
            unreached = [r for r in slot_results if not r.passed and r.name.endswith("states_reachable")]
            if unreached and reach and len(unreached) == len([r for r in slot_results if not r.passed]):
                slot_results = [r for r in slot_results if r not in unreached]
                reach_pending = True
            report.extend(slot_results)
        if not report.passed:
            return report, module, component
    if reach_pending:
        from core.machine import MachinePolicy, machine_trace

        seen: set = set()
        for ctx in contexts:
            for inst in ctx.instances:
                seen |= {s for s, _ in machine_trace(MachinePolicy(factory(ctx.problem), ctx.problem),
                                                     ctx.problem.construction_view(inst), max_steps=20_000)}
        for inst, P in reach:
            seen |= {s for s, _ in machine_trace(MachinePolicy(factory(P), P), P.construction_view(inst), max_steps=20_000)}
        states = tuple(getattr(factory(contexts[0].problem), "states", ()))
        missing = [s for s in states if s not in seen]
        if missing:
            report.add(fail("contractual", "construction_machine.states_reachable",
                            f"los estados {missing} nunca se alcanzan, ni en las micro-instancias ni en las de entrenamiento "
                            f"(greedy): revisa su prioridad y cuándo `allowed` devuelve algo, o quítalos"))
            return report, module, component
        report.add(ok("contractual", "construction_machine.states_reachable", "alcanzados en las instancias de entrenamiento"))
    where = [(ctx.instances[0], ctx.problem) for ctx in contexts if ctx.instances]
    try:
        report.extend(params_check(component, factory, where, machine_signature))
    except Exception as exc:  # noqa: BLE001
        report.add(fail("syntactic", "params_accepted", f"construir con otros valores de los parámetros lanzó {type(exc).__name__}: {exc}"))
    return report, module, component


def _class_dumps(source: str) -> tuple[dict[str, str], dict[str, Any], set[str]]:
    """({nombre de regla: AST de su clase}, {nombre: prioridad}, {nombres de las macros}). El AST va
    sin posiciones, sin su `priority` y sin los `_auto_*` que agrega la normalización (para comparar
    lo que escribió el LLM)."""
    rules, prio, macros = {}, {}, set()
    for node in ast.parse(source).body:
        if not isinstance(node, ast.ClassDef):
            continue
        name = next((b.value.value for b in node.body if isinstance(b, ast.Assign) and any(getattr(t, "id", None) == "name"
                     for t in b.targets) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str)), None)
        methods = {b.name for b in node.body if isinstance(b, ast.FunctionDef)}
        if "allowed" not in methods or not name:
            continue
        body = []
        for b in node.body:
            targets = [getattr(t, "id", "") for t in b.targets] if isinstance(b, ast.Assign) else []
            if any(t.startswith("_auto_") for t in targets):
                continue
            if "priority" in targets:
                try:
                    prio[name] = ast.literal_eval(b.value)
                except ValueError:
                    prio[name] = ast.dump(b.value)
                continue
            body.append(b)
        rules[name] = ast.dump(ast.ClassDef(node.name, node.bases, node.keywords, body, node.decorator_list),
                               include_attributes=False)
        if methods & {"start", "done"}:
            macros.add(name)
    return rules, prio, macros


def scope_check(op: str, target: str | None, parent: Individual, child_states: tuple, child_source: str) -> str | None:
    """None si el hijo respeta el alcance del operador; si no, por qué. Cada regla es una clase: el
    alcance se mira clase por clase, y la prioridad aparte."""
    ps, cs = tuple(parent.states), tuple(child_states)
    pr, pp, _ = _class_dumps(parent.source)
    cr, cp, cm = _class_dumps(child_source)
    changed = [n for n in ps if n in pr and n in cr and pr[n] != cr[n]]
    reprio = [n for n in ps if n in pp and n in cp and pp[n] != cp[n]]
    if op in ADDS:
        new = [n for n in cs if n not in ps]
        if len(cs) != len(ps) + 1 or not set(ps) <= set(cs):
            return f"{op} debe agregar exactamente una regla a {list(ps)} (el hijo tiene {list(cs)})"
        if op == "add_simple" and new[0] in cm:
            return f"add_simple agrega una regla simple (sin `start` ni `done`); `{new[0]}` es una macro"
        if op == "add_macro" and new[0] not in cm:
            return f"add_macro agrega una macro (con `start` y `done`); `{new[0]}` no los tiene"
        if changed:
            return f"{op} no cambia las reglas que ya estaban; el hijo modificó {changed}"
        if reprio:
            return f"{op} elige la prioridad de la regla nueva, no cambia las otras; el hijo cambió la de {reprio}"
    elif op == "refine_rule":
        if set(cs) != set(ps):  # el orden de la lista no importa: decide la prioridad (corrida 78)
            return f"refine_rule no cambia las reglas que hay ({list(ps)}; el hijo tiene {list(cs)})"
        others = [n for n in changed if n != target]
        if others:
            return f"refine_rule({target}) cambia solo esa regla; el hijo modificó también {others}"
        if reprio:
            return f"refine_rule({target}) no cambia prioridades; el hijo cambió la de {reprio}"
    elif op == "change_priority":
        if set(cs) != set(ps):
            return f"change_priority no cambia las reglas ({list(ps)}; el hijo tiene {list(cs)})"
        if changed:
            return f"change_priority cambia solo prioridades; el hijo modificó {changed}"
        if not reprio:
            return "change_priority debe cambiar al menos una prioridad"
    elif op == "simplify":
        if len(cs) > len(ps):
            return f"simplify no agrega reglas ({list(ps)}; el hijo tiene {list(cs)})"
    return None


# ---------------------------------------------------------------- operadores y selección
def schedule(parent: Individual, rng: Random) -> tuple[str, str | None]:
    """El operador para un hijo de `parent`: si la máquina todavía no actúa (todo en el comodín),
    agregar una regla; si tiene reglas recién agregadas, refinarlas; si no, al azar."""
    from core.machine import FALLBACK

    own = {k: v["steps"] for k, v in parent.profile.items() if k != FALLBACK}
    if not any(own.values()):
        return "add_simple", None
    macros = _class_dumps(parent.source)[2] if parent.source else set()
    pending = [s for s in parent.todo if parent.refine_failures.get(s, 0) < (MACRO_TRIES if s in macros else 2)]
    if pending:  # tras 2 refinamientos fallidos de una regla (3 si es macro) se pasa a otros operadores (corrida 67: 5 seguidos)
        return "refine_rule", pending[0]
    ops = [("add_simple", 0.15), ("add_macro", 0.25), ("refine_rule", 0.35)]
    if len(parent.states) > 1:
        ops += [("change_priority", 0.15), ("simplify", 0.1)]
    r, acc = rng.random() * sum(w for _, w in ops), 0.0
    for op, w in ops:
        acc += w
        if r <= acc:
            break
    target = None
    if op == "refine_rule":  # la regla que más pierde: exacto si hay oráculo, si no por la cota
        if parent.regret:
            cands = sorted((s for s in parent.regret if s != FALLBACK), key=lambda s: -parent.regret[s]["regret"])
        else:
            cands = sorted(own, key=lambda s: -parent.profile[s]["lost"])
        target = (cands or list(parent.states))[0]
    return op, target


def select_parent(archive: list[Individual], rng: Random) -> Individual:
    """Primero un nicho al azar (cantidad de estados; el de la máquina mínima solo si no hay otro),
    después un torneo dentro del nicho. Con un torneo sobre todo el archivo, el nicho de dos
    estados sobrevivía pero nunca se elegía como padre, así que nunca se refinaba (corrida 66)."""
    niches = sorted({x.niche for x in archive})
    if len(niches) > 1 and 0 in niches:
        niches.remove(0)
    niche = rng.choice(niches)
    return tournament([x for x in archive if x.niche == niche], rng)


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


def _attempt(path: Path, source: str, contexts, op: str, target: str | None, parent: Individual, reach=None):
    """Normaliza (números sueltos → parámetros; parámetros inertes fuera), valida y verifica el
    alcance del operador. (motivo de rechazo o None, módulo, COMPONENT, estados, fuente normalizada, notas)."""
    from core.validation.params import normalize_machine_file

    path.write_text(source)
    where = [(ctx.instances[0], ctx.problem) for ctx in contexts if ctx.instances]
    notes = normalize_machine_file(path, where)
    report, module, component = light_validation(path, contexts, reach)
    norm = path.read_text()
    if not report.passed:
        return report.feedback()[:700], module, component, (), norm, notes
    try:
        states = tuple(module.build_component(contexts[0].problem).states)
    except Exception as exc:  # noqa: BLE001
        return f"build_component(problem).states lanzó {type(exc).__name__}: {exc}", module, component, (), norm, notes
    return scope_check(op, target, parent, states, norm), module, component, states, norm, notes


def repair_prompt(op: str, target: str | None, reason: str, source: str, parent_states: tuple = ()) -> str:
    extra = ""
    if op in ADDS and parent_states:  # corrida 76: 3 add_simple reemplazaron o fusionaron la regla que había
        kind = "SIMPLE (sin `start` ni `done`)" if op == "add_simple" else "MACRO (con `start` y `done`)"
        extra = (f"\n\nPara `{op}`: deja EXACTAMENTE IGUALES las clases de las reglas que ya había ({', '.join(f'`{n}`' for n in parent_states)}"
                 f", también su `priority`), agrega UNA clase nueva ({kind}) con otro `name`, y pon las {len(parent_states) + 1} "
                 "reglas en la lista de `RuleMachine`.")
    return (f"Tu módulo (operador `{op}`{' sobre `' + target + '`' if target else ''}) fue RECHAZADO antes de evaluarse:\n\n"
            f"{reason}{extra}\n\nCorrígelo manteniendo lo que el operador pide. Devuelve UN solo bloque ```python``` con el "
            f"módulo completo.\n\n# Tu módulo\n```python\n{source}\n```")


def _rules_doc() -> str:
    import core.rules

    return (core.rules.__doc__ or "").strip()


def evolve_prompt(spec, parent: Individual, op: str, target: str | None, prof: str, trace: str, archive: list[Individual],
                  seed: bool) -> str:
    from core.machine import FALLBACK

    who = (" La base es una heurística publicada escrita a mano; devuelve un módulo nuevo con solo tu versión (puedes "
           "importar funciones de los mismos módulos)." if seed and parent.op == "base" else "")
    parts = [
        f"# Tarea\nEstás mejorando paso a paso un constructor greedy del problema **{spec.name}**, escrito como máquina de "
        f"reglas: reglas simples y macros con prioridad que, de las acciones posibles, eligen cuáles considerar (slot `{SLOT}`, "
        f"`core.rules.RuleMachine`). En cada paso se aplica UN operador a una máquina del archivo; el resultado se afina "
        f"(sus parámetros) y se compara en instancias que no ves.{who}",
        f"\n# Estructura (core.rules)\n{_rules_doc()}",
        f"\n# Operador de este paso: `{op}`\n" + OPERATOR_TEXT[op].format(target=target, fallback=FALLBACK),
        f"\nSi ninguna regla permite nada, decide el comodín del framework (`{FALLBACK}`): la acción que menos sube la cota "
        "inferior de la vista.",
        "\nLos atributos `self._auto_<nombre>` (y sus valores `_auto_<nombre> = v` en la clase) los puso el framework: son "
        "números que ya se extrajeron como parámetros (`<nombre>` en los parámetros afinados). Mantenlos tal cual. Si "
        "escribes un número suelto nuevo en un método, o un default en un `__init__` que se guarda en `self`, el framework "
        "también lo convierte en parámetro; no escribas tablas `_AUTO` ni envolturas de `build_component`.",
        f"\n# Máquina padre: `{parent.name}` (fitness {parent.fitness:.2f}, parámetros afinados {parent.params})\n"
        f"```python\n{llm_view(parent.source)}\n```",
        f"\n# Diagnóstico del padre por regla (instancias de entrenamiento)\n{prof}\n\n{trace}",
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
                 "completo: COMPONENT, las clases de las reglas y build_component(problem, **params), que devuelve "
                 "`RuleMachine(problem, [reglas...])` (`from core.rules import RuleMachine`).")
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
           tune_samples: int = 6, n_train: int = 8, n_test: int = 8, size: str | None = None, seed: str | None = None,
           base: str | None = None, rng_seed: int = 0, tokens: TokenUsage | None = None, deadline: float | None = None,
           verbose: bool = True, resume: bool = False) -> EvolveResult:
    """`resume`: seguir desde el archivo de una corrida anterior (`<workspace>/evolve_archive.json`),
    reevaluado en las mismas instancias."""
    from .generator import validate_generated_module

    ws = Path(workspace)
    tokens = tokens if tokens is not None else TokenUsage()
    rng = Random(rng_seed)
    # tamaños mezclados (`--size 5x5,6x6`): la máquina tiene que generalizar (corrida 67: la mejor ordenaba
    # sola 8 de 8 en 5×5 y 0 de 8 en 6×6, donde agotaba el tope de movimientos)
    sizes = [x.strip() for x in (size or pack.default_size).split(",") if x.strip()]
    train = [i for k, s in enumerate(sizes) for i in pack.make_instances(n_train, 9100 + 50 * k, pack.parse_size(s))]
    test = [i for k, s in enumerate(sizes) for i in pack.make_instances(n_test, 10100 + 50 * k, pack.parse_size(s))]
    contexts = [c for c in pack.make_contexts(strict=False)]
    tmp = ws / SLOT / "_evolve"
    saved = ws / "evolve_archive.json"
    reach = [(inst, pack.problem_factory(inst)) for inst in train]
    if resume and saved.exists():
        archive, is_seed = load_archive(saved, tmp, contexts[0].problem)
    else:
        root, is_seed = base_individual(pack, ws, seed, base)
        archive = [root]
    res = EvolveResult(seed=is_seed)
    for ind in archive:
        ind.params, ind.train, ind.fitness = tune(harness, ind.factory, ind.component, train, test, tune_samples, rng)
        profile(harness, ind, train)
        res.individuals.append({**ind.row(), "status": "base" if not resume else "retomado"})
    everyone = list(archive)
    last = 0.0
    for rnd in range(1, rounds + 1):
        if rnd > 1 and deadline is not None and deadline - time.monotonic() < last:
            res.individuals.append({"round": rnd, "status": "sin tiempo"})
            break
        t0 = time.monotonic()
        res.rounds = rnd
        parent = select_parent(archive, rng)
        op, target = schedule(parent, rng)
        prof, trace = profile(harness, parent, train)
        text = client.complete(SYSTEM_PROMPT, evolve_prompt(spec, parent, op, target,
                                                            profile_text(prof) + self_sorted_text(parent) + breadth_text(parent) + regret_text(parent),
                                                            trace, archive, is_seed))
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
        reason, module, component, states, source, notes = _attempt(path, blocks[0], contexts, op, target, parent, reach)
        if reason is not None:  # un turno de corrección dentro de la ronda (corrida 65: una línea `python` perdía la ronda)
            fix = client.complete(SYSTEM_PROMPT, repair_prompt(op, target, reason, blocks[0], tuple(parent.states)))
            used = getattr(client, "last_usage", None)
            if isinstance(used, TokenUsage):
                tokens.add(used)
            fixed = extract_code_blocks(fix)
            if fixed:
                reason, module, component, states, source, notes = _attempt(path, fixed[0], contexts, op, target, parent, reach)
                entry["repaired"] = reason is None
        if notes:
            entry["normalized"] = notes
        if reason is not None:
            if op == "refine_rule" and target:
                parent.refine_failures[target] = parent.refine_failures.get(target, 0) + 1
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
        child = Individual(cid, name, source, module.build_component, component, states, parent=parent.id, op=op, target=target)
        new_states = [s for s in states if s not in parent.states]
        child.todo = new_states if op in ADDS else [s for s in parent.todo if s != target and s in states]
        child.params, child.train, child.fitness = tune(harness, child.factory, component, train, test, tune_samples, rng)
        profile(harness, child, train)
        everyone.append(child)
        admitted = admit(archive, child, archive_size)
        save_archive(saved, archive, is_seed)  # un job cortado no pierde el archivo
        res.individuals.append({**child.row(), "round": rnd, "status": "archivo" if admitted else "no mejora su nicho"})
        if not admitted:
            if op == "refine_rule" and target:
                parent.refine_failures[target] = parent.refine_failures.get(target, 0) + 1
            parent.rejections.append(f"{op}{'(' + target + ')' if target else ''}: `{name}` ({', '.join(states)}) dio fitness "
                                     f"{child.fitness:.2f}; no mejora a las máquinas de {child.niche} estados del archivo")
        last = time.monotonic() - t0
        if verbose:
            print(f"[evolve] ronda {rnd}: {op}{'(' + target + ')' if target else ''} sobre {parent.name} → {name} "
                  f"({', '.join(states)}) fitness {child.fitness:.2f} {'✔' if admitted else '·'}")
    # salida: el archivo completo (para retomar con --resume) y, al workspace, las que pasen la validación completa
    save_archive(saved, archive, is_seed)
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


def save_archive(path: Path, archive: list[Individual], seed: bool) -> None:
    rows = [{"name": x.name, "source": x.source, "component": x.component, "states": list(x.states), "params": x.params,
             "fitness": _r(x.fitness), "op": x.op, "target": x.target, "todo": x.todo} for x in archive]
    path.write_text(json.dumps({"seed": seed, "archive": rows}, indent=2, ensure_ascii=False, default=str))


def load_archive(path: Path, tmp: Path, problem) -> tuple[list[Individual], bool]:
    from core.validation.params import extract_constants
    from core.validation.syntactic import load_module

    data = json.loads(path.read_text())
    tmp.mkdir(parents=True, exist_ok=True)
    out = []
    for i, row in enumerate(data["archive"]):
        f = tmp / f"resume_{i}_{row['name']}.py"
        try:  # normalizada con una versión anterior: se extiende (p.ej. los defaults de __init__)
            source, _ = extract_constants(row["source"])
        except SyntaxError:
            source = row["source"]
        f.write_text(source)
        module, r = load_module(f)
        if module is None:
            continue
        try:  # una máquina de un formato anterior (p.ej. con clase de transiciones) no se retoma
            states = tuple(module.build_component(problem).states)
        except Exception:  # noqa: BLE001
            continue
        out.append(Individual(i, row["name"], source, module.build_component, module.COMPONENT,
                              states, op=row.get("op") or "base",
                              target=row.get("target"), todo=list(row.get("todo") or [])))
    if not out:
        raise SystemExit(f"no se pudo retomar ninguna máquina de {path}")
    return out, bool(data.get("seed"))


def save_stats(workspace: str | Path, res: EvolveResult, tokens: TokenUsage, model: str = "") -> Path:
    path = Path(workspace) / "evolve_stats.json"
    runs = json.loads(path.read_text()) if path.exists() else []
    runs.append({**res.as_dict(), "tokens": tokens.as_dict(model)})
    path.write_text(json.dumps(runs, indent=2, ensure_ascii=False, default=str))
    return path


def main(pack, argv: list[str] | None = None, workspace: str | None = None, spec=None) -> EvolveResult:
    import argparse

    ap = argparse.ArgumentParser(description="Evolucionar máquinas de estados constructivas (etapa evolve)")
    ap.add_argument("--strategy", choices=["library", "machines"], default="library",
                    help="library: el LLM escribe reglas sueltas y el framework las combina (llm.library); machines: el LLM "
                         "escribe y modifica máquinas enteras")
    ap.add_argument("--choose", choices=["llm", "schedule"], default="llm",
                    help="estrategia library: quién decide la acción de cada ronda (el LLM o el calendario)")
    ap.add_argument("--seed", default=None, help="partir de una máquina escrita a mano del pack (p.ej. frg_machine)")
    ap.add_argument("--base", default=None, help="partir de una máquina generada del workspace")
    ap.add_argument("--resume", action="store_true", help="seguir desde el archivo de la corrida anterior (evolve_archive.json)")
    ap.add_argument("--rounds", type=int, default=12)
    ap.add_argument("--archive", type=int, default=4)
    ap.add_argument("--tune-samples", type=int, default=6)
    ap.add_argument("--mode", choices=["greedy", "beam"], default="greedy")
    ap.add_argument("--beam-width", type=int, default=3)
    ap.add_argument("--train", type=int, default=8)  # con 4 por tamaño el afinado sobreajustaba (corrida 76)
    ap.add_argument("--test", type=int, default=8)
    ap.add_argument("--size", default=None)
    ap.add_argument("--rng-seed", type=int, default=0)
    ap.add_argument("--workspace", default=workspace or pack.default_workspace)
    ap.add_argument("--max-minutes", type=float, default=60.0)
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
    if args.strategy == "library":
        from .library import evolve_library

        res = evolve_library(client, pack, spec or pack.make_spec(), args.workspace, Harness(pack, args.mode, args.beam_width),
                             rounds=args.rounds, tune_samples=args.tune_samples, n_train=args.train, n_test=args.test,
                             size=args.size, rng_seed=args.rng_seed, tokens=tokens, resume=args.resume,
                             deadline=time.monotonic() + 60 * args.max_minutes, choose=args.choose)
        print(json.dumps({k: v for k, v in res.as_dict().items() if k != "individuals"}, indent=2, ensure_ascii=False, default=str))
        save_stats(args.workspace, res, tokens, getattr(inner, "model", ""))
        return res
    res = evolve(client, pack, spec or pack.make_spec(), args.workspace, Harness(pack, args.mode, args.beam_width),
                 rounds=args.rounds, archive_size=args.archive, tune_samples=args.tune_samples, n_train=args.train,
                 n_test=args.test, size=args.size, seed=args.seed, base=args.base, rng_seed=args.rng_seed, tokens=tokens, resume=args.resume,
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
