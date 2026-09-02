"""Capa 1 — sintáctica (§7): el módulo importa, `COMPONENT` es válido, su
slot existe y la implementación expone los métodos del `Protocol` del slot.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from core import contracts
from core.component import ComponentSpec, ComponentSpecError

from .base import CheckResult, fail, ok

LAYER = "syntactic"

PROTOCOL_FOR_SLOT = {
    "constructor": contracts.Constructor,
    "neighborhood": contracts.Neighborhood,
    "evaluator": contracts.Evaluator,
    "acceptance": contracts.Acceptance,
    "memory": contracts.Memory,
    "perturbation": contracts.Perturbation,
    "destruction": contracts.Destruction,
    "repair_heuristic": contracts.RepairHeuristic,
    "repair_mip": contracts.RepairMIP,
    "fixing_policy": contracts.FixingPolicy,
    "stop": contracts.StopCriterion,
}


def load_module(path: str | Path) -> tuple[ModuleType | None, CheckResult]:
    """Importa un archivo .py generado por el LLM. Errores de sintaxis/import -> FAIL."""
    path = Path(path)
    name = f"_llm_component_{path.stem}_{abs(hash(str(path)))}"
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module, ok(LAYER, "import", f"{path.name} importa correctamente")
    except SyntaxError as exc:
        return None, fail(LAYER, "import", f"error de sintaxis en {path.name} línea {exc.lineno}: {exc.msg}")
    except Exception as exc:  # noqa: BLE001
        return None, fail(LAYER, "import", f"{type(exc).__name__} al importar {path.name}: {exc}")


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


def check_module(module: ModuleType) -> tuple[ComponentSpec | None, list[CheckResult]]:
    results: list[CheckResult] = []
    component = getattr(module, "COMPONENT", None)
    impl = getattr(module, "IMPL", None)
    if component is None:
        results.append(fail(LAYER, "component_present", "el módulo no define COMPONENT"))
    if impl is None:
        results.append(fail(LAYER, "impl_present", "el módulo no define IMPL"))
    if component is None or impl is None:
        return None, results
    spec, r = check_component_dict(component, impl)
    results.extend(r)
    if spec is not None:
        results.append(check_protocol(spec.slot, impl))
    return spec, results
