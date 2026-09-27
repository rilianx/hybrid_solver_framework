"""Etapa de optimización: versiones más rápidas de un modelo por piezas y de sus componentes, ya
aceptados, con el mismo comportamiento.

Primero correcto, después rápido. Lo aceptado es el oráculo: la versión optimizada tiene que dar
las mismas salidas en las mismas entradas (`core.validation.equivalence`), pasar las validaciones
de siempre y ser al menos `min_speedup` veces más rápida en la operación que el esqueleto repite.
Si no, queda la aceptada.

Mediciones del ciclo completo del CVRP (30 clientes) antes de esta etapa: el modelo generado de
rutas evaluaba 4 mil soluciones/s y el de gran tour 200 (la referencia en la misma representación:
75 mil y 11 mil); todos los vecindarios generados recalculaban el objetivo en cada `delta` (3 mil
por segundo en rutas, 200–300 en gran tour; el `relocate` escrito a mano, 39 mil).

- Modelo: se reescribe el módulo entero (`<workspace>/model/parts.py`); el anterior queda como
  `parts_slow.py`.
- Componentes: la versión rápida se guarda como la ronda siguiente del mismo nombre
  (`<slot>/<nombre>_r{k+1}.py`), que es la que carga el catálogo.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from random import Random
from typing import Any

from core.validation.base import ValidationReport, fail, ok
from core.validation.equivalence import check_component_equivalent, check_parts_equivalent, component_speed, parts_speed
from core.validation.syntactic import load_module

from .client import LLMClient, TokenUsage
from .parser import extract_code_blocks
from .prompts import MODEL_SYSTEM_PROMPT, SYSTEM_PROMPT

MODEL_TECHNIQUES = """- Evita recalcular lo mismo: memoriza por (instancia, solución) el resultado de una evaluación costosa (p.ej. un
  decodificador o un LP) y úsalo desde violations, cost_terms y aux_values (functools.lru_cache sobre argumentos
  hashables).
- Precalcula por instancia lo que no depende de la solución (matriz de distancias, demandas en listas) y guárdalo en
  una caché por instancia.
- Usa estructuras simples en los bucles internos (listas e índices en vez de dicts y objetos; evita crear tuplas o
  dicts por cada paso).
- Mantén exactamente los mismos resultados, incluidos los empates y el orden: se comparan salida por salida."""

COMPONENT_TECHNIQUES = """- Vecindario: calcula `delta` de forma INCREMENTAL, con los pocos términos que cambia el movimiento (p.ej. en rutas,
  las distancias de los arcos que se quitan y se agregan), en vez de problem.objective(apply(sol, m)) −
  problem.objective(sol). Si el movimiento puede volver infactible la solución, incluye la variación de la penalización
  (problem.penalty × variación de violations) para que delta siga siendo exactamente f(apply) − f(sol).
- Precalcula en __init__ lo que no depende de la solución.
- Mantén exactamente los mismos movimientos, en el mismo orden, y los mismos resultados de apply/undo: se comparan uno
  por uno con la versión aceptada."""


@dataclass
class OptimizationResult:
    accepted: bool = False
    rounds: int = 0
    speed_before: float = 0.0
    speed_after: float = 0.0
    reports: list[str] = field(default_factory=list)


def _ask(client: LLMClient, system: str, prompt: str, tokens: TokenUsage) -> str | None:
    text = client.complete(system, prompt)
    used = getattr(client, "last_usage", None)
    if isinstance(used, TokenUsage):
        tokens.add(used)
    blocks = extract_code_blocks(text)
    return blocks[0] if blocks else None


# ---------------------------------------------------------------- modelo
def model_prompt(source: str, speed: float, spec) -> str:
    return "\n".join([
        f"# Tarea\nEste es el modelo por piezas del problema **{spec.name}**, ya validado contra los casos de prueba. Evalúa "
        f"{speed:,.0f} soluciones por segundo (violations + cost_terms) en una instancia de tamaño realista, y las "
        "heurísticas lo llaman millones de veces. Reescríbelo para que sea bastante más rápido SIN cambiar ninguna salida.",
        f"\n# Módulo actual\n```python\n{source}\n```",
        f"\n# Técnicas\n{MODEL_TECHNIQUES}",
        "\n# Lo que se verificará\n- Mismas salidas que el módulo actual, función por función, en soluciones al azar, triviales "
        "y de los casos (incluidas vista MIP y vista constructiva), y las validaciones contra los casos de prueba.\n"
        "- Al menos 1,5 veces más evaluaciones por segundo.",
        "\nDevuelve UN solo bloque ```python``` con el módulo COMPLETO (mismos nombres de funciones).",
    ])


def optimize_model(client: LLMClient, workspace: str | Path, spec, cases: list, scale_instances: list, rounds: int = 3,
                   min_speedup: float = 1.5, tokens: TokenUsage | None = None, verbose: bool = True) -> OptimizationResult:
    from core.validation.model_parts import validate_parts

    tokens = tokens if tokens is not None else TokenUsage()
    path = Path(workspace) / "model" / "parts.py"
    old, r = load_module(path)
    if old is None:
        raise SystemExit(f"no se pudo cargar {path}: {r.message}")
    inst = scale_instances[0]
    res = OptimizationResult(speed_before=parts_speed(old, inst))
    instances = [(c.instance, [s["answer"] for s in c.solutions]) for c in cases] + [(i, []) for i in scale_instances]
    source = path.read_text()
    prompt = model_prompt(source, res.speed_before, spec)
    for rnd in range(1, rounds + 1):
        res.rounds = rnd
        src = _ask(client, MODEL_SYSTEM_PROMPT, prompt, tokens)
        if src is None:
            res.reports.append("sin bloque ```python```")
            continue
        cand = path.with_name(f"parts_opt_r{rnd}.py")
        cand.write_text(src)
        new, r = load_module(cand)
        report = ValidationReport(subject=cand.name)
        report.add(r)
        if new is not None:
            report = validate_parts(new, cases, scale_instances=scale_instances, decoder=spec.decoder)
            if report.passed:
                report = check_parts_equivalent(old, new, instances)
            if report.passed:
                speed = parts_speed(new, inst)
                if speed < min_speedup * res.speed_before:
                    report.add(fail("speed", "faster", f"{speed:,.0f} evaluaciones/s contra {res.speed_before:,.0f}: se pide al menos "
                                                       f"{min_speedup:g} veces más"))
                else:
                    res.speed_after = speed
                    report.add(ok("speed", "faster", f"{speed:,.0f} contra {res.speed_before:,.0f} evaluaciones/s"))
        if report.passed:
            path.with_name("parts_slow.py").write_text(source)
            path.write_text(src)
            res.accepted = True
            if verbose:
                print(f"[optimizar/modelo] ✔ ronda {rnd}: {res.speed_before:,.0f} → {res.speed_after:,.0f} evaluaciones/s")
            return res
        res.reports.append(report.feedback())
        if verbose:
            print(f"[optimizar/modelo] ✘ ronda {rnd}: {report.failed_layer}")
        prompt = (f"La versión optimizada fue RECHAZADA. Corrígela y devuelve el módulo completo en un único bloque ```python```."
                  f"\n\n# Reporte\n{report.feedback()}\n\n# Módulo original (el oráculo)\n```python\n{source}\n```"
                  f"\n\n# Tu versión rechazada\n```python\n{src}\n```\n\n# Técnicas\n{MODEL_TECHNIQUES}")
    return res


# ---------------------------------------------------------------- componentes
OPTIMIZABLE = ("neighborhood", "greedy_score", "perturbation", "destruction")


def latest_components(workspace: str | Path, slots=OPTIMIZABLE) -> list[tuple[str, str, Path, int]]:
    """(slot, nombre base, archivo de la ronda más alta, ronda) de cada componente del workspace."""
    latest: dict[tuple[str, str], tuple[Path, int]] = {}
    for slot in slots:
        for path in sorted((Path(workspace) / slot).glob("*.py")):
            base, _, rnd = path.stem.rpartition("_r")
            if not base or not rnd.isdigit():
                continue
            if (slot, base) not in latest or int(rnd) > latest[(slot, base)][1]:
                latest[(slot, base)] = (path, int(rnd))
    return [(slot, base, p, k) for (slot, base), (p, k) in sorted(latest.items())]


def component_prompt(slot: str, source: str, speed: float, spec, model_source: str) -> str:
    unit = {"neighborhood": "delta/s", "greedy_score": "construcciones/s", "perturbation": "perturbaciones/s",
            "destruction": "destrucciones/s"}[slot]
    return "\n".join([
        f"# Tarea\nEste componente (slot `{slot}`) del problema **{spec.name}** ya está validado. Hace {speed:,.0f} {unit} en una "
        "instancia de tamaño realista, y el esqueleto lo llama cientos de miles de veces por corrida. Reescríbelo para que "
        "sea bastante más rápido SIN cambiar ninguna salida.",
        f"\n# Componente actual\n```python\n{source}\n```",
        f"\n# Modelo del problema (lo que ve el componente)\n```python\n{model_source}\n```",
        f"\n# Técnicas\n{COMPONENT_TECHNIQUES}",
        "\n# Lo que se verificará\n- Mismas salidas que el componente actual, uno por uno (movimientos y su orden, apply, undo, "
        "delta; o puntajes; o resultados con la misma semilla), y las validaciones del slot.\n- Al menos 1,5 veces más rápido.",
        "\nDevuelve UN solo bloque ```python``` con el módulo COMPLETO (mismo COMPONENT, mismo build_component).",
    ])


def optimize_components(client: LLMClient, pack, workspace: str | Path, rounds: int = 2, min_speedup: float = 1.5,
                        slots=("neighborhood",), tokens: TokenUsage | None = None, verbose: bool = True) -> dict[str, dict]:
    from .generator import validate_generated_module

    tokens = tokens if tokens is not None else TokenUsage()
    spec = pack.make_model_spec()
    model_source = pack.make_spec().problem_model_source
    inst = pack.make_instances(1, 4242, pack.parse_size(pack.default_size))[0]
    P = pack.problem_factory(inst)
    sols = [P.parts.trivial_solution(inst)] + [P.parts.random_solution(inst, Random(s)) for s in range(4)]
    contexts = pack.make_contexts(strict=False)
    out: dict[str, dict] = {}
    for slot, base, path, k in latest_components(workspace, slots):
        old_mod, r = load_module(path)
        if old_mod is None:
            continue
        make_old = lambda p, m=old_mod: m.build_component(p)  # noqa: E731
        before = component_speed(slot, make_old, pack.problem_factory, inst, sols[1])
        res = OptimizationResult(speed_before=before)
        source = path.read_text()
        prompt = component_prompt(slot, source, before, spec, model_source)
        for rnd in range(1, rounds + 1):
            res.rounds = rnd
            src = _ask(client, SYSTEM_PROMPT, prompt, tokens)
            if src is None:
                res.reports.append("sin bloque ```python```")
                continue
            cand = path.with_name(f"{base}_r{k + rnd}.py")
            cand.write_text(src)
            report, new_mod, new_comp = validate_generated_module(cand, contexts)
            # el catálogo y las configuraciones ya elegidas buscan el componente por nombre (corrida 41:
            # el LLM lo renombró "…_fast" y las configuraciones de la run 32 ya no lo encontraban)
            old_comp = {k: v for k, v in old_mod.COMPONENT.items() if k != "combination_gains"}
            if report.passed and {k: v for k, v in (new_comp or {}).items() if k != "combination_gains"} != old_comp:
                report.add(fail("equivalence", "same_component_metadata",
                                f"COMPONENT tiene que quedar idéntico al original (mismo nombre, slot, esqueletos y parámetros): {old_comp}"))
            if report.passed:
                report = check_component_equivalent(slot, old_mod.build_component(pack.problem_factory(inst)),
                                                    new_mod.build_component(pack.problem_factory(inst)), pack.problem_factory(inst), sols)
            if report.passed:
                after = component_speed(slot, lambda p, m=new_mod: m.build_component(p), pack.problem_factory, inst, sols[1])
                if after < min_speedup * before:
                    report.add(fail("speed", "faster", f"{after:,.0f} contra {before:,.0f} por segundo: se pide al menos {min_speedup:g} veces más"))
                else:
                    res.speed_after = after
            if report.passed:
                res.accepted = True
                # las rondas rechazadas intermedias no deben quedar como la más alta
                for j in range(1, rnd):
                    path.with_name(f"{base}_r{k + j}.py").unlink(missing_ok=True)
                if rnd > 1:
                    cand.rename(path.with_name(f"{base}_r{k + 1}.py"))
                if verbose:
                    print(f"[optimizar/{slot}] ✔ {base}: {before:,.0f} → {res.speed_after:,.0f}/s")
                break
            res.reports.append(report.feedback())
            cand.unlink(missing_ok=True)
            if verbose:
                print(f"[optimizar/{slot}] ✘ {base} ronda {rnd}: {report.failed_layer}")
            prompt = (f"La versión optimizada fue RECHAZADA. Corrígela y devuelve el módulo completo en un único bloque ```python```."
                      f"\n\n# Reporte\n{report.feedback()}\n\n# Componente original (el oráculo)\n```python\n{source}\n```"
                      f"\n\n# Tu versión rechazada\n```python\n{src}\n```\n\n# Técnicas\n{COMPONENT_TECHNIQUES}")
        out[f"{slot}/{base}"] = {"accepted": res.accepted, "rounds": res.rounds, "before": round(res.speed_before, 1),
                                 "after": round(res.speed_after, 1), "rejections": res.reports}
    return out


__all__ = ["OptimizationResult", "latest_components", "optimize_components", "optimize_model"]
