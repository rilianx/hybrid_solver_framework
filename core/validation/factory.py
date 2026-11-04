"""Lo que se exige a un componente ya cargado (un módulo Python o uno C++ envuelto, `native/check.py`): las capas
sobre `factory(problem)` en cada micro-contexto, la sonda grande, la diversidad contra los aceptados y la combinación
con cada esqueleto."""

from __future__ import annotations

import dataclasses
from typing import Any

from core.validation import ValidationContext, ValidationReport, validate_component
from core.validation.base import fail, ok
from core.validation.diversity import improving_neighbors
from core.validation.quality import diversity_check, probe_checks


def validate_factory(component: dict, factory, contexts: list[ValidationContext], peers: list[tuple[str, Any]] | None = None,
                     report: ValidationReport | None = None) -> ValidationReport:
    """Las capas sobre `factory(problem)` en cada micro-contexto, la sonda, la diversidad contra `peers` y la
    combinación: lo que se exige a un componente después de cargarlo (un módulo Python o uno C++ envuelto)."""
    report = report or ValidationReport(subject=f"componente '{component.get('name', '?')}'")

    # Todas las propiedades deben cumplirse en TODOS los micro-contextos, salvo
    # `neighborhood.improves_from_start`, que basta con que se cumpla en UNO: la
    # solución trivial de algún contexto puede ser un óptimo local para movimientos
    # elementales (nada mejora desde ahí), y exigirlo en todos volvía el gate
    # insatisfacible para operadores legítimos (corrida 4: `single_setup_removal_r1`).
    AGGREGATE_ANY = {"neighborhood.improves_from_start"}
    reports: list[ValidationReport] = []
    for k, ctx0 in enumerate(contexts):
        ctx = dataclasses.replace(ctx0, accepted_peers=list(peers or [])) if peers else ctx0
        try:
            impl = factory(ctx.problem)
        except Exception as exc:  # noqa: BLE001
            report.add(fail("syntactic", "factory_runs", f"build_component(problem) lanzó {type(exc).__name__}: {exc} (micro-instancia {k})"))
            return report
        reports.append(validate_component(component, impl, ctx))
        hard_fail = [r for r in reports[-1].failures() if r.name not in AGGREGATE_ANY]
        if hard_fail:
            report.extend(reports[-1].results)
            return report
    report.add(ok("syntactic", "factory_runs"))

    probe = contexts[0].diversity_probe if contexts else None
    slot_name = component.get("slot", "")

    any_fails = [r for rep in reports for r in rep.failures() if r.name in AGGREGATE_ANY]
    if any_fails and len(any_fails) == len(reports):
        # Falló en todos los micro-contextos. Última oportunidad: la sonda grande. Corrida 7:
        # `same_period_setup_swap` no mejoraba desde la partida en 3×5 (18 movimientos, ninguno
        # mejora) pero sí en 10×15 (73 mejoras, todas novedosas); rechazado, el modelo lo
        # "arregló" rellenándolo con flips. La micro-instancia era chica para ese operador.
        rescued = _improves_on_probe(factory, probe, slot_name)
        if rescued is None:
            report.extend(reports[0].results)  # trae el hint con movimientos que sí mejoran
            return report
        report.add(rescued)

    # Diversidad: sobre la sonda (instancia grande) y con el componente reconstruido allí.
    # Se hace una sola vez, después de las propiedades: rechazar por duplicado a algo que
    # además está mal implementado sería el feedback equivocado.
    if probe is not None:
        try:
            probe_impl = factory(probe.problem)
            report.extend(probe_checks(slot_name, probe_impl, probe))
            if report.passed and peers:
                report.extend(diversity_check(
                    slot_name, probe_impl, peers, probe.solution,
                    probe.problem, probe.max_similarity, probe.min_novelty,
                ))
        except Exception as exc:  # noqa: BLE001 — la sonda no debe tumbar la validación
            report.add(ok("quality", "probe_skipped", f"{type(exc).__name__}: {exc}"))
        if not report.passed:
            return report

    # Combinación: el componente dentro de cada esqueleto que declara, desde varias partidas.
    # Poda `compatible_skeletons` a donde es útil; rechaza si no es útil en ninguno.
    combo = contexts[0].combination if contexts else None
    if combo is not None:
        from core.validation.combination import SLOT_SKELETONS, check_combinations

        if slot_name in SLOT_SKELETONS:
            try:
                results, keep, gains = check_combinations(component, factory, combo)
            except Exception as exc:  # noqa: BLE001 — una excepción del componente es un rechazo
                report.add(fail("quality", f"{slot_name}.useful_in_some_skeleton",
                                f"el componente lanzó {type(exc).__name__} dentro de un esqueleto: {exc}"))
                return report
            report.extend(results)
            if not report.passed:
                return report
            component["compatible_skeletons"] = keep
            component["combination_gains"] = gains

    if reports:
        # aprobado: se reporta el último contexto, sin los fallos agregables que quedaron compensados
        report.extend([r for r in reports[-1].results if r.name not in AGGREGATE_ANY or r.passed])
    return report


def _improves_on_probe(factory, probe, slot_name: str):
    """OK si el vecindario tiene mejoras desde la partida de la sonda; None si no (o no aplica)."""
    if probe is None or slot_name != "neighborhood":
        return None
    try:
        imp = improving_neighbors(factory(probe.problem), probe.solution, probe.problem)
    except Exception:  # noqa: BLE001
        return None
    if not imp:
        return None
    return ok("quality", "neighborhood.improves_from_start",
              f"sin mejoras desde la partida en las micro-instancias, pero {len(imp)} en la sonda "
              f"({len(probe.solution)}×{len(probe.solution[0])}): las micro-instancias eran chicas para este operador")
