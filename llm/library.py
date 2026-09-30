"""Estrategia `library` de la etapa `evolve`: el LLM escribe piezas y el framework las combina.

    biblioteca ← {}                                         # reglas (piezas), no máquinas
    repetir:
        operador ← new_rule | refine_rule(r)
        pieza    ← LLM(biblioteca, mejor composición y su diagnóstico por rollout, operador)
        validación liviana (la pieza es una máquina de UNA regla) → a la biblioteca
        compositor (sin LLM): las combinaciones de hasta 3 piezas que la incluyen, en todos los
                     órdenes de prioridad, con el greedy en train → la mejor composición se afina
    al final: la mejor composición → workspace (un módulo que carga sus piezas)

Por qué así (corridas 72–78): diseñando la máquina entera, la primera regla del LLM salía ancha
(permitía el 72–75 % de los candidatos) y cada paso hacia dos reglas angostas empeoraba antes de
mejorar. A mano, el camino a FRG es monótono y corto: mínima 83,0 → `bg` sola 74,7 → `bg` (100)
+ `reduce` (50) 18,4, contra 18,3 de FRG completo (5×5 + 6×6). Son dos piezas angostas y un orden:
el LLM escribe cada pieza sola ("¿qué tipo de movimiento falta?") y el compositor prueba los
órdenes, así que el LLM no razona sobre prioridades ni pasa por valles.
"""

from __future__ import annotations

import ast
import json
import time
from dataclasses import dataclass, field
from itertools import permutations
from pathlib import Path
from random import Random
from typing import Any

from core.validation.params import llm_view

from .client import LLMClient, TokenUsage
from .evolve import SLOT, EvolveResult, Harness, _r, light_validation, tune
from .parser import extract_code_blocks
from .prompts import SYSTEM_PROMPT

MAX_PIECES = 3  # una composición combina hasta 3 piezas
LIBRARY_MAX = 8  # piezas en la biblioteca (se sacan las que no aparecen en las mejores composiciones)
PRIORITIES = tuple(100 // 2 ** k for k in range(4))  # prioridad de cada posición de una composición: 100, 50, 25, 12
BROAD = 0.5  # una pieza que permite en promedio más de esta fracción de los candidatos es ancha: solo va al final
N_EXAMPLES = 4

OPERATOR_TEXT = {
    "choose": (
        "Decide tú qué hacer en esta ronda: escribir una pieza NUEVA (un tipo de movimiento que falta) o MEJORAR una pieza "
        "de la biblioteca (di cuál; su código está abajo si está en la mejor máquina). Usa la evidencia: movimientos de "
        "más por pieza (en total y por paso), qué piezas permitían la mejor alternativa y el historial de rondas anteriores. "
        "Una pieza nueva tiene que ser ANGOSTA: de los candidatos permite solo los de su tipo y devuelve [] cuando no "
        "aplica. Al mejorar una pieza, mantén su `name`; la versión nueva entra junto a la anterior. Empieza la respuesta "
        "con dos líneas:\nACCIÓN: nueva   (o)   ACCIÓN: mejorar <name de la pieza>\nPOR QUÉ: <una línea>\ny después el "
        "bloque de código."),
    "new_rule": (
        "Escribe UNA pieza NUEVA: un tipo de movimiento. Tiene que ser ANGOSTA: de los candidatos permite solo los de su "
        "tipo y devuelve [] cuando no aplica; lo demás lo cubren otras piezas o el comodín. Mira los pasos de abajo donde "
        "la mejor alternativa es un movimiento que NINGUNA pieza permite (o solo una ANCHA): ¿de qué tipo es? No repitas una pieza "
        "que ya está."),
    "refine_rule": (
        "Mejora la pieza `{target}` (abajo), manteniendo su `name`. En los pasos donde ella decidió mal: si la mejor "
        "alternativa no estaba entre lo que permitió, cambia el set (angostar o ampliar); si estaba, cambia el orden. La versión nueva "
        "entra junto a la anterior."),
}


@dataclass
class Piece:
    """Una regla de la biblioteca: un módulo cuyo `build_component` devuelve `RuleMachine(problem, [regla])`."""

    id: int
    rule: str  # el `name` de su regla
    name: str  # COMPONENT["name"] del módulo
    source: str
    factory: Any
    component: dict
    macro: bool = False
    op: str = "new_rule"
    parent: int | None = None
    params: dict = field(default_factory=dict)
    alone: float = float("inf")  # fitness sola (con el comodín), en train
    doc: str = ""
    width: float = 0.0  # fracción media de los candidatos que permite cuando aplica

    @property
    def key(self) -> str:
        return f"p{self.id}"

    def row(self) -> dict:
        return {"id": self.id, "rule": self.rule, "name": self.name, "op": self.op, "parent": self.parent,
                "macro": self.macro, "alone": _r(self.alone), "width": round(self.width, 3), "params": self.params}

    @property
    def broad(self) -> bool:
        return self.width > BROAD


def composition_factory(pieces: tuple[Piece, ...]):
    """(fábrica, COMPONENT) de la máquina que combina `pieces` con prioridades en ese orden. Los
    parámetros de cada pieza van con su prefijo (`p3::w_bad`)."""
    from core.rules import RuleMachine

    def factory(problem, **params):
        rules = []
        for k, pc in enumerate(pieces):
            sub = {name.split("::", 1)[1]: v for name, v in params.items() if name.startswith(pc.key + "::")}
            rule = pc.factory(problem, **{**pc.params, **sub}).rules[0]
            rule.priority = PRIORITIES[k]  # la prioridad la pone el compositor
            rules.append(rule)
        return RuleMachine(problem, rules)

    specs = {}
    for pc in pieces:
        for name, spec in (pc.component.get("params") or {}).items():
            specs[f"{pc.key}::{name}"] = dict(spec, default=pc.params.get(name, spec.get("default")))
    comp = {"name": "+".join(pc.rule for pc in pieces), "slot": SLOT, "compatible_skeletons": ["CONSTRUCT"],
            "requires": [], "params": specs}
    return factory, comp


SCREEN_KEEP = 25  # combinaciones nuevas que pasan del filtro (4 instancias) al train completo


def compose(harness: Harness, library: list[Piece], instances, cache: dict, must: Piece | None = None,
            deadline: float | None = None, screen=None, best: tuple[int, ...] | None = None) -> list[tuple[float, tuple[int, ...]]]:
    """Las combinaciones de hasta MAX_PIECES piezas (las que incluyen `must`, si se da) en todos los
    órdenes, con el greedy en `instances`. Dos versiones de la misma regla no se combinan, y una
    pieza ancha solo va al final: arriba siempre aplica y las demás nunca actuarían (corrida 79: las
    10 mejores composiciones empataban en 51,812, con la ancha primero). Devuelve el caché completo
    ordenado: [(media, ids en orden de prioridad)].

    Con `screen` (unas pocas instancias), las combinaciones nuevas se filtran primero ahí y solo las
    SCREEN_KEEP mejores se evalúan en `instances`: el compositor se lleva casi todo el tiempo de una
    ronda (corrida 83: al retomar, recalcular la biblioteca entera agotó el job en 3 rondas)."""
    by_id = {pc.id: pc for pc in library}
    pending = []
    for k in range(1, MAX_PIECES + 1):
        for combo in permutations(library, k):
            ids = tuple(pc.id for pc in combo)
            if ids in cache or (must is not None and must not in combo) or len({pc.rule for pc in combo}) < k:
                continue
            if any(pc.broad for pc in combo[:-1]):  # una pieza ancha tapa a las de abajo (corrida 79): solo al final
                continue
            if deadline is not None and time.monotonic() > deadline:
                break
            pending.append(combo)
    if screen is not None and len(pending) > SCREEN_KEEP:
        scored = sorted(((harness.mean(composition_factory(c)[0], {}, screen), i) for i, c in enumerate(pending)),
                        key=lambda t: t[0])
        pending = [pending[i] for _, i in scored[:SCREEN_KEEP]]
    # la pieza nueva insertada en cada posición de la mejor máquina (hasta MAX_PIECES + 1 piezas): una pieza
    # que complementa a las que funcionan no tiene que desplazar a ninguna (corrida 86: la mejor ya usaba 3)
    if must is not None and best and must.id not in best and all(i in by_id for i in best):
        for pos in range(len(best) + 1):
            combo = tuple(by_id[i] for i in best[:pos]) + (must,) + tuple(by_id[i] for i in best[pos:])
            ids = tuple(pc.id for pc in combo)
            if ids in cache or len({pc.rule for pc in combo}) < len(combo) or any(pc.broad for pc in combo[:-1]):
                continue
            pending.append(combo)
    for combo in pending:
        if deadline is not None and time.monotonic() > deadline:
            break
        cache[tuple(pc.id for pc in combo)] = harness.mean(composition_factory(combo)[0], {}, instances)
    return sorted(((v, ids) for ids, v in cache.items() if all(i in by_id for i in ids)), key=lambda t: t[0])


def _rule_info(source: str) -> tuple[str, bool]:
    """(docstring de la clase de la regla, ¿es macro?)"""
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef):
            methods = {b.name for b in node.body if isinstance(b, ast.FunctionDef)}
            if "allowed" in methods:
                return (ast.get_docstring(node) or "").split("\n")[0], bool(methods & {"start", "done"})
    return "", False


def library_text(library: list[Piece], best: tuple[int, ...] | None) -> str:
    if not library:
        return "(vacía: la máquina es solo el comodín)"
    lines = []
    for pc in sorted(library, key=lambda p: p.alone):
        where = f", posición {best.index(pc.id) + 1} de la mejor" if best and pc.id in best else ""
        lines.append(f"- `{pc.rule}` #{pc.id}{' (ANCHA)' if pc.broad else ''}: "
                     f"{pc.doc or '—'} Permite el {pc.width:.0%} de los candidatos, sola {pc.alone:.1f}{where}.")
    return "\n".join(lines)


def measure_piece(harness: Harness, pc: Piece, train) -> None:
    """Ancho de la pieza sola (en train): qué fracción de los candidatos permite cuando aplica."""
    from core.machine import MachinePolicy
    from core.rules import rule_breadth

    share = applies = 0.0
    for inst in train[:4]:
        P = harness.pack.problem_factory(inst)
        try:
            b = rule_breadth(MachinePolicy(composition_factory((pc,))[0](P), P), P.construction_view(inst))
        except Exception:  # noqa: BLE001
            b = None
        row = (b or {}).get(pc.rule) or {}
        share += row.get("share", 0.0)
        applies += row.get("applies", 0)
    pc.width = share / applies if applies else 0.0


def _show(partial) -> str:
    """El estado para el prompt: sus pilas si las tiene (CPMP), si no su repr."""
    stacks = getattr(partial, "stacks", None)
    return str(stacks) if stacks is not None else repr(partial)


ROLLOUT_PER_SIZE = 1  # instancias de train de cada tamaño donde se compara por rollout
ROLLOUT_STEPS = 12  # pasos muestreados por instancia


def rollout_evidence(harness: Harness, pieces: tuple[Piece, ...], library: list[Piece], instances) -> tuple[str, dict]:
    """La evidencia: en pasos muestreados de la construcción greedy de la máquina (`pieces`; vacía = el
    comodín solo), cada candidato se completa con la misma máquina (rollout). Si otra acción termina con
    menos movimientos que la elegida, es un contraejemplo. Sin oráculo exacto: corrida 85, con el óptimo
    solo en 5×5 la máquina parecía perfecta ("acierta siempre cuando sus piezas aplican") y la pérdida
    estaba en 6×6; el rollout vale en cualquier tamaño y compara contra lo que la máquina misma lograría.
    ("texto", {regla: movimientos de más}, {regla: pasos muestreados})."""
    from core.construction import GreedyConstructor
    from core.machine import FALLBACK, _diverse
    from core.rules import RuleMachine, action_key

    if not instances:
        return "", {}, {}
    factory = composition_factory(pieces)[0] if pieces else (lambda P, **_: RuleMachine(P, []))
    rows, regret, steps_by, found = [], {}, {}, 0
    for inst in instances:
        P = harness.pack.problem_factory(inst)
        view = P.construction_view(inst)
        g = GreedyConstructor(P, factory(P), max_steps=20_000)
        pol = g.policy
        pol.bind(view)
        partial = view.empty()
        memory = pol.init(partial)
        trail = []
        for _ in range(20_000):  # la construcción greedy, guardando cada paso
            if view.is_complete(partial):
                break
            cands = list(view.candidates(partial))
            if not cands:
                break
            scores = g.scores(partial, cands, memory)
            a = cands[min(range(len(cands)), key=scores.__getitem__)]
            trail.append((partial, memory, cands, a, pol.state_of(partial, memory)))
            memory = pol.update(partial, memory, a)
            partial = view.apply(partial, a)
        stride = max(1, len(trail) // ROLLOUT_STEPS)

        def finish(p, mem, act):
            pol.bind(view)
            m2 = pol.update(p, mem, act)
            sol = g.complete_from(view, view.apply(p, act), Random(0), memory=m2, fresh=False)[0]
            return float(P.objective(sol)) if P.is_feasible(sol) else float("inf")

        for p, mem, cands, a, st in trail[::stride]:
            base = finish(p, mem, a)
            alts = [(finish(p, mem, c), c) for c in cands if action_key(c) != action_key(a)]
            steps_by[st] = steps_by.get(st, 0) + 1
            if not alts:
                continue
            v, b = min(alts, key=lambda t: t[0])
            if v < base:
                found += 1
                regret[st] = regret.get(st, 0) + (base - v)
                allow = []
                for pc in library:
                    m = RuleMachine(P, [pc.factory(P, **pc.params).rules[0]])
                    m.bind(view)
                    mm = m.entry(pc.rule, p, m.initial(p)[1][0])
                    if any(action_key(x) == action_key(b) for x in m.allowed(pc.rule, p, mm)):
                        allow.append(f"`{pc.rule}` #{pc.id}" + (" (ANCHA)" if pc.broad else ""))
                rows.append((base - v, st, p, a, base, b, v, allow, view.apply(p, a), view.apply(p, b)))
    if not steps_by:
        return "", {}, {}
    lines = [f"Comparando por rollout (cada acción completada con la misma máquina): "
             f"en {found} de {sum(steps_by.values())} pasos muestreados otra acción termina con menos movimientos ("
             + ", ".join(f"`{st}` {regret.get(st, 0):g} de más en {n} pasos" for st, n in steps_by.items()) + ")."]
    for d, st, p, a, base, b, v, allow, pa, pb in _diverse(sorted(rows, key=lambda t: -t[0]), N_EXAMPLES, key=lambda t: t[1]):
        who = "el comodín" if st == FALLBACK else f"`{st}`"
        lines.append(f"- estado `{_show(p)}`; decidió {who}.\n"
                     f"  eligió {a!r} → `{_show(pa)}`, y la máquina termina en {base:g} movimientos\n"
                     f"  con {b!r} → `{_show(pb)}` terminaría en {v:g}; lo permite"
                     f"{'n' if len(allow) > 1 else ''} {', '.join(allow) if allow else 'NINGUNA pieza'}")
    return "\n".join(lines), regret, steps_by


def loss_table(pieces, regret, steps) -> str:
    """Movimientos de más por paso que decidió cada pieza (por rollout): arriba del prompt, para que se vea
    qué pieza pierde más (corrida 86: la de reducción perdía 2,4 por paso en 6×6 contra 1 de `bg`, pero el
    LLM solo escribía piezas nuevas)."""
    from core.machine import FALLBACK

    rows = [f"| {'comodín' if n == FALLBACK else '`' + n + '`'} | {regret.get(n, 0) / steps[n]:.2f} | {steps[n]} |"
            for n in [p.rule for p in pieces] + [FALLBACK] if steps.get(n)]
    if not rows:
        return ""
    return ("Movimientos de más por paso que decidió cada pieza (por rollout; mayor = pierde más):\n"
            "| pieza | por paso | pasos muestreados |\n|---|---|---|\n" + "\n".join(rows) + "\n\n")


def api_summary(source: str) -> str:
    """Las clases de la vista con su docstring y los campos, sin el código de los métodos."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source
    out = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        fields = [ast.unparse(b) for b in node.body if isinstance(b, ast.AnnAssign)]
        doc = ast.get_docstring(node) or ""
        methods = [b.name for b in node.body if isinstance(b, ast.FunctionDef) and not b.name.startswith("_")]
        out.append(f"class {node.name}:  " + "; ".join(fields) + (f"\n    {doc}" if doc else "")
                   + (f"\n    métodos: {', '.join(methods)}" if methods and not doc else ""))
    return "\n\n".join(out)


EXAMPLE = '''
COMPONENT = {"name": "<nombre descriptivo>", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"],
             "requires": [], "params": {}}

from core.rules import RuleMachine


class MiRegla:
    """Una línea: qué tipo de movimiento permite."""

    name = "<nombre de la regla>"

    def allowed(self, partial, memory, candidates):   # los de su tipo, en orden de preferencia; [] = no aplica
        return [a for a in candidates if ...]

    # opcional: def score(self, partial, memory, action) -> float  (menor = mejor; si no, vale el orden)


def build_component(problem, **params):
    return RuleMachine(problem, [MiRegla()])
'''


def library_prompt(spec, op: str, target: Piece | None, library: list[Piece], best: tuple[int, ...] | None,
                   best_fitness: float, evid: str, rejections: list[str], history: list[str] | None = None) -> str:
    order = " > ".join(f"`{next(p.rule for p in library if p.id == i)}`" for i in best) if best else "solo el comodín"
    parts = [
        f"# Tarea\nConstructor greedy para **{spec.name}**, armado con piezas. Cada pieza es UNA regla: de los candidatos "
        f"permite los de un tipo de movimiento. El framework prueba combinaciones de hasta {MAX_PIECES} piezas de la "
        "biblioteca y se queda con la mejor; lo que ninguna permite lo decide el comodín (la acción que menos sube la cota "
        "inferior).",
        f"\n# Operador: `{op}`\n" + OPERATOR_TEXT[op].format(target=target.rule if target else ""),
        f"\n# Biblioteca\n{library_text(library, best)}",
        f"\n# Mejor máquina: {order}, {best_fitness:.1f} movimientos (menor = mejor)\n{evid}",
    ]
    if target is not None:
        parts.append(f"\n# Pieza a mejorar: `{target.rule}` #{target.id}\n```python\n{llm_view(target.source)}\n```")
    if op == "choose" and best:
        for i in best:
            pc = next(p for p in library if p.id == i)
            parts.append(f"\n# Pieza `{pc.rule}` #{pc.id} (en la mejor máquina)\n```python\n{llm_view(pc.source)}\n```")
    if history:
        parts.append("\n# Rondas anteriores\n" + "\n".join(f"- {h}" for h in history[-6:]))
    parts += [f"\n# Formato\n```python\n{EXAMPLE}```", f"\n# Problema\n{spec.description}"]
    if spec.construction_source:
        parts.append(f"\n# Estado parcial y acción\n```python\n{api_summary(spec.construction_source)}\n```")
    if rejections:
        parts.append("\n# Rechazados hace poco\n" + "\n".join(f"- {r[:200]}" for r in rejections[-2:]))
    parts.append("\nDevuelve UN bloque ```python``` con el módulo completo de la pieza (COMPONENT con un nombre nuevo, la "
                 "clase y build_component). Todo número que decide algo va en COMPONENT['params'] con 'range' y 'default'.")
    return "\n".join(parts)


def _act(op: str, target) -> str:
    return f"mejorar `{target.rule}`" if op == "refine_rule" and target is not None else "pieza nueva"


def parse_choice(text: str, library: list[Piece], best_pieces: tuple) -> tuple[str, Any, str | None]:
    """(operador, pieza a mejorar o None, motivo) de las líneas `ACCIÓN:` y `POR QUÉ:` de la respuesta. Sin
    una acción legible, o si la pieza nombrada no existe, es una pieza nueva."""
    import re

    m = re.search(r"ACCI[OÓ]N\s*:\s*(nueva|mejorar)\s*`?([\w.-]*)`?", text, re.I)
    why = re.search(r"POR\s+QU[EÉ]\s*:\s*(.+)", text, re.I)
    why = why.group(1).strip()[:200] if why else None
    if m and m.group(1).lower() == "mejorar" and m.group(2):
        name = m.group(2)
        cands = [p for p in best_pieces if p.rule == name] or [p for p in library if p.rule == name]
        if cands:
            return "refine_rule", cands[-1], why
    return "new_rule", None, why


def _attempt_piece(path: Path, source: str, contexts, op: str, target: Piece | None, library: list[Piece], reach):
    """(motivo de rechazo o None, módulo, COMPONENT, nombre de la regla, fuente normalizada)."""
    from core.validation.params import normalize_machine_file

    path.write_text(source)
    where = [(ctx.instances[0], ctx.problem) for ctx in contexts if ctx.instances]
    normalize_machine_file(path, where)
    report, module, component = light_validation(path, contexts, reach)
    norm = path.read_text()
    if not report.passed:
        return report.feedback()[:700], module, component, None, norm
    try:
        rules = module.build_component(contexts[0].problem).rules
    except Exception as exc:  # noqa: BLE001
        return f"build_component(problem) lanzó {type(exc).__name__}: {exc}", module, component, None, norm
    if len(rules) != 1:
        return (f"una pieza es UNA regla: build_component devuelve RuleMachine(problem, [regla]) con una sola (tiene "
                f"{len(rules)}: {[r.name for r in rules]})"), module, component, None, norm
    rule = rules[0].name
    if callable(getattr(rules[0], "start", None)) or callable(getattr(rules[0], "done", None)):
        return ("una pieza es una regla simple, sin `start` ni `done`: se evalúa en cada paso con `allowed` (y `score` "
                "si hace falta)"), module, component, None, norm
    if op == "new_rule" and any(pc.rule == rule for pc in library):
        return f"ya hay una pieza `{rule}` en la biblioteca: una regla nueva necesita otro `name` (y otro tipo de movimiento)", \
            module, component, None, norm
    if op == "refine_rule" and target is not None and rule != target.rule:
        return f"refine_rule({target.rule}) mantiene el `name` de la regla (el hijo se llama `{rule}`)", module, component, None, norm
    return None, module, component, rule, norm


def repair_prompt(op: str, reason: str, source: str) -> str:
    return (f"Tu pieza (operador `{op}`) fue RECHAZADA antes de evaluarse:\n\n{reason}\n\nCorrígela: UNA regla, en un "
            f"módulo completo. Devuelve UN solo bloque ```python```.\n\n# Tu módulo\n```python\n{source}\n```")


def save_library(path: Path, library: list[Piece], cache: dict | None = None, state: dict | None = None,
                 key: str = "") -> None:
    """La biblioteca y, para retomar sin recalcular, las composiciones ya evaluadas y la mejor."""
    rows = [{**pc.row(), "source": pc.source, "component": pc.component} for pc in library]
    data = {"library": rows, "key": key, "cache": [[list(ids), v] for ids, v in (cache or {}).items()],
            "state": {k: (list(v) if k == "best" and v else v) for k, v in (state or {}).items()}}
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def load_saved(path: Path, key: str) -> tuple[dict, dict | None, dict]:
    """(caché de composiciones, mejor composición, {id: fila}) de una corrida anterior; el caché y la mejor
    solo si se evaluaron con las mismas instancias (`key`)."""
    data = json.loads(path.read_text())
    rows = {r["id"]: r for r in data.get("library", [])}
    if data.get("key") != key:
        return {}, None, rows
    cache = {tuple(ids): float(v) for ids, v in data.get("cache", [])}
    st = data.get("state") or None
    if st and st.get("best"):
        st = dict(st, best=tuple(st["best"]))
    return cache, st, rows


def load_library(path: Path, tmp: Path, problem) -> list[Piece]:
    from core.validation.syntactic import load_module

    tmp.mkdir(parents=True, exist_ok=True)
    out = []
    for row in json.loads(path.read_text()).get("library", []):
        f = tmp / f"lib_{row['id']}_{row['rule']}.py"
        f.write_text(row["source"])
        module, _ = load_module(f)
        if module is None:
            continue
        try:
            rules = module.build_component(problem).rules
        except Exception:  # noqa: BLE001
            continue
        doc, macro = _rule_info(row["source"])
        out.append(Piece(row["id"], rules[0].name, row["name"], row["source"], module.build_component, module.COMPONENT,
                         macro=macro, op=row.get("op") or "new_rule", parent=row.get("parent"),
                         params=dict(row.get("params") or {}), doc=doc))
    return out


def composed_module(pieces: tuple[Piece, ...], params: dict, name: str) -> str:
    """Un módulo que carga sus piezas (archivos `lib_p<id>.py` junto a él) y las combina."""
    _, comp = composition_factory(pieces)
    comp = dict(comp, name=name)
    for k, v in params.items():
        if k in comp["params"]:
            comp["params"][k] = dict(comp["params"][k], default=v)
    files = [(f"lib_{pc.key}.py", pc.key) for pc in pieces]
    return f'''"""Máquina compuesta por la estrategia `library` de evolve: {' > '.join(pc.rule for pc in pieces)}."""

COMPONENT = {comp!r}

import importlib.util
from pathlib import Path

from core.rules import RuleMachine

_PIECES = {files!r}


def _load(fname):
    path = Path(__file__).with_name(fname)
    spec = importlib.util.spec_from_file_location("_piece_" + path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_MODULES = [(_load(f), key) for f, key in _PIECES]


def build_component(problem, **params):
    rules = []
    for k, (mod, key) in enumerate(_MODULES):
        sub = {{n.split("::", 1)[1]: v for n, v in params.items() if n.startswith(key + "::")}}
        rule = mod.build_component(problem, **sub).rules[0]
        rule.priority = 100 // 2 ** k  # en el orden del compositor
        rules.append(rule)
    return RuleMachine(problem, rules)
'''


def evolve_library(client: LLMClient, pack, spec, workspace: str | Path, harness: Harness, rounds: int = 12,
                   tune_samples: int = 6, n_train: int = 8, n_test: int = 8, size: str | None = None, rng_seed: int = 0,
                   tokens: TokenUsage | None = None, deadline: float | None = None, verbose: bool = True,
                   resume: bool = False, choose: str = "llm") -> EvolveResult:
    """`choose`: "llm" = el LLM decide en cada ronda si escribe una pieza nueva o mejora cuál;
    "schedule" = el calendario (55 % nueva, 45 % mejorar la pieza de la mejor máquina que más pierde)."""
    from core.rules import RuleMachine

    from .generator import validate_generated_module

    ws = Path(workspace)
    tokens = tokens if tokens is not None else TokenUsage()
    rng = Random(rng_seed)
    sizes = [x.strip() for x in (size or pack.default_size).split(",") if x.strip()]
    train = [i for k, s in enumerate(sizes) for i in pack.make_instances(n_train, 9100 + 50 * k, pack.parse_size(s))]
    test = [i for k, s in enumerate(sizes) for i in pack.make_instances(n_test, 10100 + 50 * k, pack.parse_size(s))]
    contexts = list(pack.make_contexts(strict=False))
    tmp = ws / SLOT / "_library"
    tmp.mkdir(parents=True, exist_ok=True)
    saved = ws / "evolve_library.json"
    reach = [(inst, pack.problem_factory(inst)) for inst in train]
    key = f"{','.join(sizes)}|{n_train}"
    library = load_library(saved, tmp, contexts[0].problem) if resume and saved.exists() else []
    cache, prev, rows = load_saved(saved, key) if library else ({}, None, {})
    res = EvolveResult()
    screen = train[:: max(1, len(train) // 4)][:4]
    minimal = harness.mean(lambda P, **_: RuleMachine(P, []), {}, train)
    per = max(1, len(train) // max(1, len(sizes)))  # train va por tamaño: las primeras de cada uno
    rollout_insts = [i for k in range(len(sizes)) for i in train[k * per:k * per + ROLLOUT_PER_SIZE]]
    for pc in library:
        row = rows.get(pc.id) or {}
        if prev is not None and row.get("alone") is not None:  # ya medida con estas instancias
            pc.alone, pc.width = float(row["alone"]), float(row.get("width") or 0.0)
        else:
            pc.alone = cache.setdefault((pc.id,), harness.mean(composition_factory((pc,))[0], {}, train))
            measure_piece(harness, pc, train)
        res.individuals.append({**pc.row(), "status": "retomada"})
    ranked = compose(harness, library, train, cache, deadline=deadline, screen=screen) if library else []
    state = {"best": None, "fitness": float("inf"), "train": minimal, "params": {}}
    if prev is not None and prev.get("best") and all(any(p.id == i for p in library) for i in prev["best"]):
        state.update(best=prev["best"], fitness=float(prev["fitness"]), train=float(prev["train"]),
                     params=dict(prev.get("params") or {}))

    def update_best(ranked):
        """La mejor composición en train, si mejora a la actual (al principio, al comodín solo): se afina."""
        if not ranked or ranked[0][0] >= state["train"] or ranked[0][1] == state["best"]:
            return False
        ids = ranked[0][1]
        pieces = tuple(next(p for p in library if p.id == i) for i in ids)
        factory, comp = composition_factory(pieces)
        params, tr, te = tune(harness, factory, comp, train, test, tune_samples, rng)
        for pc in pieces:  # los parámetros afinados vuelven a sus piezas
            pc.params = {**pc.params, **{k.split("::", 1)[1]: v for k, v in params.items() if k.startswith(pc.key + "::")}}
        state.update(best=ids, fitness=te, train=min(tr, ranked[0][0]), params=params)
        return True

    update_best(ranked)
    rejections: list[str] = []
    history: list[str] = []
    next_id = max([pc.id for pc in library], default=-1) + 1
    last = 0.0
    for rnd in range(1, rounds + 1):
        if rnd > 1 and deadline is not None and deadline - time.monotonic() < last:
            res.individuals.append({"round": rnd, "status": "sin tiempo"})
            break
        t0 = time.monotonic()
        res.rounds = rnd
        best_pieces = tuple(next(p for p in library if p.id == i) for i in state["best"]) if state["best"] else ()
        if len(library) < 2:  # sin dos piezas no hay nada que combinar
            op, target = "new_rule", None
        elif choose == "llm":  # el LLM decide qué hacer (se lee de su respuesta)
            op, target = "choose", None
        elif rng.random() < 0.55:
            op, target = "new_rule", None
        else:
            op = "refine_rule"
            target = best_pieces[0] if best_pieces else rng.choice(library)
        # evidencia por rollout en la mejor máquina (o en el comodín solo), anotada por pieza
        evid, regret, steps = rollout_evidence(harness, best_pieces, library, rollout_insts)
        evid = loss_table(best_pieces, regret, steps) + evid
        if best_pieces and op == "refine_rule" and regret:  # la pieza de la mejor máquina que más pierde
            worst = max((s for s in regret if s in {p.rule for p in best_pieces}), default=None, key=regret.get)
            target = next((p for p in best_pieces if p.rule == worst), target)
        prompt = library_prompt(spec, op, target, library, state["best"], state["fitness"] if best_pieces else minimal,
                                evid, rejections, history)
        text = client.complete(SYSTEM_PROMPT, prompt)
        used = getattr(client, "last_usage", None)
        if isinstance(used, TokenUsage):
            tokens.add(used)
        why = None
        if op == "choose":  # la acción que eligió el LLM
            op, target, why = parse_choice(text, library, best_pieces)
        entry = {"round": rnd, "op": op, "target": target.rule if target else None, "why": why}
        blocks = extract_code_blocks(text)
        if not blocks:
            rejections.append(f"{op}: la respuesta no traía un bloque ```python```")
            res.individuals.append({**entry, "status": "sin código"})
            continue
        path = tmp / f"cand_{next_id}.py"
        reason, module, component, rule, source = _attempt_piece(path, blocks[0], contexts, op, target, library, reach)
        if reason is not None:
            fix = client.complete(SYSTEM_PROMPT, repair_prompt(op, reason, blocks[0]))
            used = getattr(client, "last_usage", None)
            if isinstance(used, TokenUsage):
                tokens.add(used)
            fixed = extract_code_blocks(fix)
            if fixed:
                reason, module, component, rule, source = _attempt_piece(path, fixed[0], contexts, op, target, library, reach)
                entry["repaired"] = reason is None
        if reason is not None:
            rejections.append(f"{op}{'(' + target.rule + ')' if target else ''}: {reason}")
            history.append(f"ronda {rnd}: {_act(op, target)} → rechazada ({reason.splitlines()[-1][:90]})")
            res.individuals.append({**entry, "status": "rechazado", "reason": reason})
            last = time.monotonic() - t0
            if verbose:
                print(f"[library] ronda {rnd}: {op} ✘ {reason[:160]}")
            continue
        doc, macro = _rule_info(source)
        pc = Piece(next_id, rule, component.get("name") or f"piece_{next_id}", source, module.build_component, component,
                   macro=macro, op=op, parent=target.id if target else None, doc=doc)
        next_id += 1
        pc.alone = cache.setdefault((pc.id,), harness.mean(composition_factory((pc,))[0], {}, train))
        measure_piece(harness, pc, train)
        library.append(pc)
        ranked = compose(harness, library, train, cache, must=pc, deadline=deadline, screen=screen, best=state["best"])
        improved = update_best(ranked)
        mine = next((v for v, ids in ranked if pc.id in ids), float("inf"))
        # biblioteca acotada: fuera las piezas que no están en ninguna de las mejores composiciones
        if len(library) > LIBRARY_MAX:
            keep = {i for _, ids in ranked[: 3 * LIBRARY_MAX] for i in ids}
            drop = sorted((p for p in library if p.id not in keep), key=lambda p: -p.alone)
            for p in drop[: len(library) - LIBRARY_MAX]:
                library.remove(p)
        save_library(saved, library, cache, state, key)
        status = "mejor máquina" if improved else "en la biblioteca"
        history.append(f"ronda {rnd}: {_act(op, target)} → `{rule}` #{pc.id}: sola {pc.alone:.1f}, mejor combinación con "
                       f"ella {mine:.1f} en train; {'NUEVA MEJOR MÁQUINA' if improved else 'no mejora a la mejor'} "
                       f"({state['train']:.1f} en train)")
        res.individuals.append({**entry, **pc.row(), "best_with": _r(mine), "status": status,
                                "best": [next(p.rule for p in library if p.id == i) for i in state["best"]] if state["best"] else [],
                                "fitness": _r(state["fitness"])})
        last = time.monotonic() - t0
        if verbose:
            print(f"[library] ronda {rnd}: {op} → `{rule}` sola {pc.alone:.2f}, mejor combinación con ella {mine:.2f}; "
                  f"mejor máquina {state['fitness']:.2f} {'✔' if improved else '·'}")
    # salida: la biblioteca (para retomar) y la mejor máquina, como un módulo que carga sus piezas
    save_library(saved, library, cache, state, key)
    if state["best"]:
        # la mejor, y si no pasa la validación completa (corrida 82: una pieza útil en 5×5 y 6×6 nunca se
        # activa en las micro-instancias), la siguiente composición en train que sí la pase
        by_id = {p.id: p for p in library}
        tries = [state["best"]] + [ids for _, ids in ranked[:10] if ids != state["best"]]
        out_dir = ws / SLOT
        out_dir.mkdir(parents=True, exist_ok=True)
        for k, ids in enumerate(t for t in tries if all(i in by_id for i in t)):
            pieces = tuple(by_id[i] for i in ids)
            for p in pieces:
                (out_dir / f"lib_{p.key}.py").write_text(p.source)
            name = "library_" + "_".join(p.rule for p in pieces)
            path = out_dir / f"{name}_r1.py"
            params = state["params"] if k == 0 else {}
            path.write_text(composed_module(pieces, params, name))
            report, _, _ = validate_generated_module(path, contexts)
            fitness = state["fitness"] if k == 0 else harness.mean(composition_factory(pieces)[0], {}, test)
            row = {"name": name, "path": str(path), "fitness": _r(fitness), "params": params}
            if report.passed:
                res.archive = [p.rule for p in pieces]
                res.written.append(row)
                break
            path.unlink()
            res.written.append({**row, "path": None, "rejected": report.feedback()[:400]})
    res.individuals.append({"library": [p.row() for p in library], "best": res.archive, "fitness": _r(state["fitness"]),
                            "minimal": _r(minimal), "compositions": [(_r(v), list(ids)) for v, ids in ranked[:10]]})
    return res


__all__ = ["Piece", "compose", "composition_factory", "evolve_library", "library_prompt", "composed_module", "OPERATOR_TEXT"]
