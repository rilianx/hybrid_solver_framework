"""Orquestación de las capas (§7): se avanza capa por capa y se detiene en
la primera que falla, porque las capas siguientes asumen la anterior
(no tiene sentido medir propiedades contractuales de algo que no cumple
el Protocol, ni calidad de algo que lanza excepciones).

Tres puntos de entrada, según qué se está validando:

- `validate_component(component_dict, impl, ctx)` — un componente de un slot:
  sintáctica → contractual (→ operativa del time_limit si es repair_mip).
- `validate_problem_model(ctx)` — el `ProblemModel` generado: semántica MIP.
- `validate_variant(runner, ctx)` — una variante ensamblada: operativa → calidad.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import ValidationContext, ValidationReport
from .contractual import check_slot
from .operational import VariantRunner, check_repair_mip_time_limit, check_variant_runs
from .quality import check_component_quality, check_min_quality
from .semantic_mip import check_problem_model_mip
from .syntactic import check_component_dict, check_module, check_protocol, load_module


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
    report.extend(check_component_quality(spec.slot, impl, ctx))
    return report


def validate_component_file(path: str | Path, ctx: ValidationContext) -> ValidationReport:
    """Variante para un archivo .py generado por el LLM (con COMPONENT e IMPL)."""
    report = ValidationReport(subject=f"archivo '{Path(path).name}'")
    module, r = load_module(path)
    report.add(r)
    if module is None:
        return report
    spec, results = check_module(module)
    report.extend(results)
    if spec is None or not report.passed:
        return report
    impl = module.IMPL
    report.extend(check_slot(spec.slot, impl, ctx))
    if not report.passed:
        return report
    if spec.slot == "repair_mip":
        report.extend(check_repair_mip_time_limit(impl, ctx, time_limit=1.0))
        if not report.passed:
            return report
    report.extend(check_component_quality(spec.slot, impl, ctx))
    return report


def validate_problem_model(ctx: ValidationContext) -> ValidationReport:
    report = ValidationReport(subject=f"ProblemModel {type(ctx.problem).__name__}")
    report.extend(check_problem_model_mip(ctx))
    return report


def validate_variant(runner: VariantRunner, ctx: ValidationContext, name: str = "variante", budget_seconds: float = 2.0) -> ValidationReport:
    report = ValidationReport(subject=name)
    report.extend(check_variant_runs(runner, ctx, budget_seconds=budget_seconds))
    if not report.passed:
        return report
    report.extend(check_min_quality(runner, ctx, budget_seconds=budget_seconds))
    return report
