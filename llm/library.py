"""Estrategia `library` de la etapa `evolve`: el LLM escribe piezas y el framework las combina.

    biblioteca ← {}                                         # reglas (piezas), no máquinas
    repetir:
        operador ← new_rule | refine_rule(r)
        pieza    ← LLM(biblioteca, mejor composición y su diagnóstico con el oráculo, operador)
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
from .evolve import (SLOT, EvolveResult, Harness, Individual, _r, breadth_text, light_validation, profile, profile_text,
                     regret_text, self_sorted_text, tune)
from .parser import extract_code_blocks
from .prompts import SYSTEM_PROMPT, protocol_source, slot_hint

MAX_PIECES = 3  # una composición combina hasta 3 piezas
LIBRARY_MAX = 8  # piezas en la biblioteca (se sacan las que no aparecen en las mejores composiciones)
PRIORITIES = tuple(100 // 2 ** k for k in range(3))  # prioridad de cada posición de una composición: 100, 50, 25

OPERATOR_TEXT = {
    "new_rule": (
        "Escribe UNA regla NUEVA para la biblioteca: un tipo de movimiento. El compositor del framework la combina con "
        "las otras piezas (hasta 3 por máquina, en todos los órdenes de prioridad) y se queda con la mejor combinación, "
        "así que tú NO eliges prioridades ni escribes las otras reglas. Una regla buena es ANGOSTA: de los candidatos "
        "permite solo los de su tipo (en orden de preferencia, o con `score`) y devuelve [] cuando no aplica; lo que no "
        "cubre lo cubren las otras piezas o el comodín. Mira los contraejemplos de la mejor máquina: ¿qué tipo de "
        "movimiento hace el óptimo en esos pasos que ninguna pieza de la biblioteca permite? No repitas una pieza que ya "
        "está. Si el tipo de movimiento se sostiene varios pasos sobre el mismo objetivo, puede ser una macro "
        "(`start`/`done`)."),
    "refine_rule": (
        "Mejora la pieza `{target}` de la biblioteca (su versión actual está abajo). Mantén su `name`. Mira su "
        "precisión y los contraejemplos donde ella decidió: si el óptimo no estaba entre lo que permitió, cambia el set "
        "(angostar o ampliar); si estaba, cambia el orden. Puedes convertirla en macro (`start` fija su objetivo, "
        "`done` dice cuándo terminó) si el óptimo sostiene su tipo de movimiento varios pasos sobre el mismo objetivo. "
        "La versión nueva entra a la biblioteca junto a la anterior; el compositor elige."),
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

    @property
    def key(self) -> str:
        return f"p{self.id}"

    def row(self) -> dict:
        return {"id": self.id, "rule": self.rule, "name": self.name, "op": self.op, "parent": self.parent,
                "macro": self.macro, "alone": _r(self.alone), "params": self.params}


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


def compose(harness: Harness, library: list[Piece], instances, cache: dict, must: Piece | None = None,
            deadline: float | None = None) -> list[tuple[float, tuple[int, ...]]]:
    """Las combinaciones de hasta MAX_PIECES piezas (las que incluyen `must`, si se da) en todos los
    órdenes, con el greedy en `instances`. Dos versiones de la misma regla no se combinan. Devuelve
    el caché completo ordenado: [(media, ids en orden de prioridad)]."""
    by_id = {pc.id: pc for pc in library}
    for k in range(1, MAX_PIECES + 1):
        for combo in permutations(library, k):
            ids = tuple(pc.id for pc in combo)
            if ids in cache or (must is not None and must not in combo) or len({pc.rule for pc in combo}) < k:
                continue
            if deadline is not None and time.monotonic() > deadline:
                break
            factory, _ = composition_factory(combo)
            cache[ids] = harness.mean(factory, {}, instances)
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
    lines = ["| pieza | tipo | qué hace | fitness sola (con el comodín) | en la mejor máquina |", "|---|---|---|---|---|"]
    for pc in sorted(library, key=lambda p: p.alone):
        where = f"posición {best.index(pc.id) + 1}" if best and pc.id in best else "—"
        lines.append(f"| `{pc.rule}` (#{pc.id}) | {'macro' if pc.macro else 'simple'} | {pc.doc or '—'} | {pc.alone:.2f} | {where} |")
    return "\n".join(lines) if library else "(vacía: todavía no hay piezas; la máquina es solo el comodín)"


EXAMPLE = '''
COMPONENT = {"name": "<nombre descriptivo>", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"],
             "requires": [], "params": {}}

from core.rules import RuleMachine


class MiRegla:
    """Una línea: qué tipo de movimiento permite."""

    name = "<nombre de la regla>"

    def allowed(self, partial, memory, candidates):
        return [a for a in candidates if ...]      # solo los de su tipo, en orden de preferencia; [] = no aplica


def build_component(problem, **params):
    return RuleMachine(problem, [MiRegla()])
'''


def library_prompt(spec, op: str, target: Piece | None, library: list[Piece], best: tuple[int, ...] | None,
                   best_fitness: float, diag: str, trace: str, rejections: list[str]) -> str:
    import core.rules
    from core.machine import FALLBACK

    order = " > ".join(f"`{next(p.rule for p in library if p.id == i)}`" for i in best) if best else "(solo el comodín)"
    parts = [
        f"# Tarea\nEstás construyendo, pieza por pieza, un constructor greedy del problema **{spec.name}**. Cada pieza es UNA "
        f"regla (`core.rules`): de las acciones posibles permite las de un tipo. El framework combina las piezas de la "
        f"biblioteca (hasta {MAX_PIECES}, en todos los órdenes de prioridad) y se queda con la mejor máquina; lo que "
        f"ninguna pieza permite lo decide el comodín (`{FALLBACK}`: la acción que menos sube la cota inferior).",
        f"\n# Estructura (core.rules)\n{(core.rules.__doc__ or '').strip()}",
        f"\n# Operador de este paso: `{op}`\n" + OPERATOR_TEXT[op].format(target=target.rule if target else ""),
        f"\n# Biblioteca\n{library_text(library, best)}",
        f"\n# Mejor máquina: {order} (fitness {best_fitness:.2f}, menor = mejor)\n{diag}\n\n{trace}",
    ]
    if target is not None:
        parts.append(f"\n# Pieza a mejorar: `{target.rule}` (#{target.id})\n```python\n{llm_view(target.source)}\n```")
    parts += [
        f"\n# Formato de una pieza\n```python\n{EXAMPLE}```\nUna macro agrega `start(partial, memory) -> memoria` y "
        "`done(partial, memory) -> bool`; `init`, `update` y `score` son opcionales. No pongas `priority`: la pone el "
        "compositor.",
        f"\n# Contrato del slot\n```python\n{protocol_source(SLOT)}```",
        "\n# Reglas\n" + slot_hint(spec, SLOT),
        f"\n# Problema\n{spec.description}",
    ]
    if spec.construction_source:
        parts.append(f"\n## Vista constructiva: el estado parcial y la acción\n```python\n{spec.construction_source}\n```")
    if rejections:
        parts.append("\n# Intentos ya rechazados (no los repitas)\n" + "\n".join(f"- {r}" for r in rejections[-4:]))
    parts.append("\nDevuelve UN solo bloque ```python``` con el módulo completo de la pieza: COMPONENT (un nombre "
                 "descriptivo nuevo), la clase de la regla y build_component(problem, **params), que devuelve "
                 "`RuleMachine(problem, [TuRegla(...)])` con UNA sola regla.")
    return "\n".join(parts)


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
    if op == "new_rule" and any(pc.rule == rule for pc in library):
        return f"ya hay una pieza `{rule}` en la biblioteca: una regla nueva necesita otro `name` (y otro tipo de movimiento)", \
            module, component, None, norm
    if op == "refine_rule" and target is not None and rule != target.rule:
        return f"refine_rule({target.rule}) mantiene el `name` de la regla (el hijo se llama `{rule}`)", module, component, None, norm
    return None, module, component, rule, norm


def repair_prompt(op: str, reason: str, source: str) -> str:
    return (f"Tu pieza (operador `{op}`) fue RECHAZADA antes de evaluarse:\n\n{reason}\n\nCorrígela: UNA regla, en un "
            f"módulo completo. Devuelve UN solo bloque ```python```.\n\n# Tu módulo\n```python\n{source}\n```")


def save_library(path: Path, library: list[Piece]) -> None:
    rows = [{**pc.row(), "source": pc.source, "component": pc.component} for pc in library]
    path.write_text(json.dumps({"library": rows}, indent=2, ensure_ascii=False, default=str))


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
                   resume: bool = False) -> EvolveResult:
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
    library = load_library(saved, tmp, contexts[0].problem) if resume and saved.exists() else []
    res = EvolveResult()
    cache: dict = {}
    minimal = harness.mean(lambda P, **_: RuleMachine(P, []), {}, train)
    for pc in library:
        pc.alone = cache.setdefault((pc.id,), harness.mean(composition_factory((pc,))[0], {}, train))
        res.individuals.append({**pc.row(), "status": "retomada"})
    ranked = compose(harness, library, train, cache, deadline=deadline) if library else []
    state = {"best": None, "fitness": float("inf"), "train": minimal, "params": {}}

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
    next_id = max([pc.id for pc in library], default=-1) + 1
    last = 0.0
    for rnd in range(1, rounds + 1):
        if rnd > 1 and deadline is not None and deadline - time.monotonic() < last:
            res.individuals.append({"round": rnd, "status": "sin tiempo"})
            break
        t0 = time.monotonic()
        res.rounds = rnd
        best_pieces = tuple(next(p for p in library if p.id == i) for i in state["best"]) if state["best"] else ()
        if len(library) < 2 or rng.random() < 0.55:  # sin dos piezas no hay nada que combinar
            op, target = "new_rule", None
        else:
            op = "refine_rule"
            target = best_pieces[0] if best_pieces else rng.choice(library)
        # diagnóstico de la mejor máquina (o del comodín solo)
        if best_pieces:
            factory, comp = composition_factory(best_pieces)
            ind = Individual(-1, comp["name"], "", factory, comp, tuple(p.rule for p in best_pieces), params={})
        else:
            ind = Individual(-1, "minimal", "", lambda P, **_: RuleMachine(P, []), {"params": {}}, ())
        prof, trace = profile(harness, ind, train)
        if best_pieces and op == "refine_rule" and ind.regret:  # la pieza de la mejor máquina que más pierde
            worst = max((s for s in ind.regret if s in {p.rule for p in best_pieces}), default=None,
                        key=lambda s: ind.regret[s]["regret"])
            target = next((p for p in best_pieces if p.rule == worst), target)
        diag = profile_text(prof) + self_sorted_text(ind) + breadth_text(ind) + regret_text(ind)
        prompt = library_prompt(spec, op, target, library, state["best"], state["fitness"] if best_pieces else minimal,
                                diag, trace, rejections)
        text = client.complete(SYSTEM_PROMPT, prompt)
        used = getattr(client, "last_usage", None)
        if isinstance(used, TokenUsage):
            tokens.add(used)
        entry = {"round": rnd, "op": op, "target": target.rule if target else None}
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
        library.append(pc)
        ranked = compose(harness, library, train, cache, must=pc, deadline=deadline)
        improved = update_best(ranked)
        mine = next((v for v, ids in ranked if pc.id in ids), float("inf"))
        # biblioteca acotada: fuera las piezas que no están en ninguna de las mejores composiciones
        if len(library) > LIBRARY_MAX:
            keep = {i for _, ids in ranked[: 3 * LIBRARY_MAX] for i in ids}
            drop = sorted((p for p in library if p.id not in keep), key=lambda p: -p.alone)
            for p in drop[: len(library) - LIBRARY_MAX]:
                library.remove(p)
        save_library(saved, library)
        status = "mejor máquina" if improved else "en la biblioteca"
        res.individuals.append({**entry, **pc.row(), "best_with": _r(mine), "status": status,
                                "best": [next(p.rule for p in library if p.id == i) for i in state["best"]] if state["best"] else [],
                                "fitness": _r(state["fitness"])})
        last = time.monotonic() - t0
        if verbose:
            print(f"[library] ronda {rnd}: {op} → `{rule}` sola {pc.alone:.2f}, mejor combinación con ella {mine:.2f}; "
                  f"mejor máquina {state['fitness']:.2f} {'✔' if improved else '·'}")
    # salida: la biblioteca (para retomar) y la mejor máquina, como un módulo que carga sus piezas
    save_library(saved, library)
    if state["best"]:
        pieces = tuple(next(p for p in library if p.id == i) for i in state["best"] if any(p.id == i for p in library))
        out_dir = ws / SLOT
        out_dir.mkdir(parents=True, exist_ok=True)
        for p in pieces:
            (out_dir / f"lib_{p.key}.py").write_text(p.source)
        name = "library_" + "_".join(p.rule for p in pieces)
        path = out_dir / f"{name}_r1.py"
        path.write_text(composed_module(pieces, state["params"], name))
        report, _, _ = validate_generated_module(path, contexts)
        res.archive = [p.rule for p in pieces]
        row = {"name": name, "path": str(path), "fitness": _r(state["fitness"]), "params": state["params"]}
        if not report.passed:
            row["rejected"] = report.feedback()[:400]
        res.written.append(row)
    res.individuals.append({"library": [p.row() for p in library], "best": res.archive, "fitness": _r(state["fitness"]),
                            "minimal": _r(minimal), "compositions": [(_r(v), list(ids)) for v, ids in ranked[:10]]})
    return res


__all__ = ["Piece", "compose", "composition_factory", "evolve_library", "library_prompt", "composed_module", "OPERATOR_TEXT"]
