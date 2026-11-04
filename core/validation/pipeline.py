"""Orquestación de las capas (§7): se avanza capa por capa y se detiene en
la primera que falla, porque las capas siguientes asumen la anterior
(no tiene sentido medir propiedades contractuales de algo que no cumple
el Protocol, ni calidad de algo que lanza excepciones).

`validate_component(component_dict, impl, ctx)` valida un componente de un slot: sintáctica → contractual
(→ operativa del time_limit si es repair_mip) → calidad. El modelo del problema se valida aparte
(`core.validation.model_parts`, `native/check_model.py`).
"""

from __future__ import annotations

from typing import Any

from .base import ValidationContext, ValidationReport, guard
from .contractual import check_slot
from .operational import check_repair_mip_time_limit
from .quality import check_component_quality
from .syntactic import check_component_dict, check_protocol


def validate_component(component: dict[str, Any], impl: Any, ctx: ValidationContext, stop_at_first_failed_layer: bool = True) -> ValidationReport:
    report = ValidationReport(subject=f"componente '{component.get('name', '?')}'")
    spec, results = check_component_dict(component, impl)
    report.extend(results)
    if spec is None:
        return report
    report.add(check_protocol(spec.slot, impl))
    if stop_at_first_failed_layer and not report.passed:
        return report

    report.extend(check_slot(spec.slot, impl, ctx))
    if stop_at_first_failed_layer and not report.passed:
        return report

    if spec.slot == "repair_mip":
        report.extend(check_repair_mip_time_limit(impl, ctx, time_limit=1.0))
        if stop_at_first_failed_layer and not report.passed:
            return report
    report.extend(_quality(spec.slot, impl, ctx))
    return report


def _quality(slot: str, impl: Any, ctx: ValidationContext):
    """La capa de calidad llama al componente (moves, delta, build...) y una excepción suya es
    un rechazo, no un error del validador: sin esto un vecindario generado que lanzaba
    `ValueError` en `delta` tumbaba la generación completa (CVRP, corrida 17)."""
    return guard("quality", f"{slot}.quality", lambda: check_component_quality(slot, impl, ctx))
