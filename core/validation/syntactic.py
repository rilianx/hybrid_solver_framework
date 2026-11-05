"""Capa 1 — sintáctica (§7): el módulo importa, `COMPONENT` es válido, su
slot existe y la implementación expone los métodos del `Protocol` del slot.
"""

from __future__ import annotations

from typing import Any

from core import contracts
from core.component import ComponentSpec, ComponentSpecError

from .base import CheckResult, fail, ok

LAYER = "syntactic"

PROTOCOL_FOR_SLOT = {
    "constructor": contracts.Constructor,
    "tiebreak": contracts.TieBreak,
    "neighborhood": contracts.Neighborhood,
    "evaluator": contracts.Evaluator,
    "acceptance": contracts.Acceptance,
    "memory": contracts.Memory,
    "perturbation": contracts.Perturbation,
    "relink": contracts.Relink,
    "destruction": contracts.Destruction,
    "repair_heuristic": contracts.RepairHeuristic,
    "repair_mip": contracts.RepairMIP,
    "stop": contracts.StopCriterion,
}


def check_component_dict(component: dict[str, Any], impl: Any) -> tuple[ComponentSpec | None, list[CheckResult]]:
    try:
        spec = ComponentSpec.from_dict(component, impl)
    except ComponentSpecError as exc:
        return None, [fail(LAYER, "component_schema", str(exc))]
    return spec, [ok(LAYER, "component_schema", f"slot={spec.slot}, {len(spec.params)} parámetros")]


def check_protocol(slot: str, impl: Any) -> CheckResult:
    """`impl` puede ser una instancia o una clase; se verifica la presencia de métodos."""
    protocol = PROTOCOL_FOR_SLOT[slot]
    required = [
        name
        for name in getattr(protocol, "__protocol_attrs__", set()) or _protocol_methods(protocol)
        if not name.startswith("_")
    ]
    missing = [m for m in required if not callable(getattr(impl, m, None))]
    if missing:
        return fail(LAYER, "protocol", f"la implementación no define {missing} exigidos por {protocol.__name__}")
    return ok(LAYER, "protocol", f"cumple {protocol.__name__} ({', '.join(sorted(required))})")


def _protocol_methods(protocol: type) -> set[str]:
    return {
        name
        for name, value in vars(protocol).items()
        if callable(value) and not name.startswith("_")
    }
