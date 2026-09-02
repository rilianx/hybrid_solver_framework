"""Bloque de metadatos de auto-descripción de componentes (§4) y su registro.

Cada componente generado por el LLM viene acompañado de un diccionario
`COMPONENT` con esta forma:

    COMPONENT = {
        "name": "two_opt_sampled",
        "slot": "neighborhood",
        "compatible_skeletons": ["HC", "SA", "TS", "ILS", "VNS"],
        "requires": ["ProblemModel.permutation_view"],
        "params": {
            "sample_size": {"type": "int", "range": [10, 500], "log": True},
            "strategy":    {"type": "cat", "values": ["first", "best"]},
        },
    }

`ComponentSpec` valida y normaliza ese diccionario; `ComponentRegistry`
agrupa specs por slot y sabe filtrar por esqueleto compatible, lo que
alimenta tanto al ensamblador (`core.skeleton`) como al exportador del
espacio de configuración (`config_space`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

VALID_PARAM_TYPES = {"int", "float", "cat", "bool"}

# Slots reconocidos por el núcleo (tabla de la sección 4).
KNOWN_SLOTS = {
    "constructor",
    "neighborhood",
    "evaluator",
    "acceptance",
    "memory",
    "perturbation",
    "destruction",
    "repair_heuristic",
    "repair_mip",
    "fixing_policy",
    "stop",
}


class ComponentSpecError(ValueError):
    """El diccionario COMPONENT no respeta el esquema esperado."""


def _validate_param(name: str, spec: dict[str, Any]) -> None:
    ptype = spec.get("type")
    if ptype not in VALID_PARAM_TYPES:
        raise ComponentSpecError(
            f"parámetro '{name}': type debe ser uno de {VALID_PARAM_TYPES}, recibido {ptype!r}"
        )
    if ptype in ("int", "float"):
        rng = spec.get("range")
        if not (isinstance(rng, (list, tuple)) and len(rng) == 2):
            raise ComponentSpecError(
                f"parámetro '{name}' de tipo {ptype} requiere 'range': [min, max]"
            )
        lo, hi = rng
        if lo > hi:
            raise ComponentSpecError(f"parámetro '{name}': range inválido {rng}")
    elif ptype == "cat":
        values = spec.get("values")
        if not isinstance(values, (list, tuple)) or len(values) == 0:
            raise ComponentSpecError(f"parámetro '{name}' de tipo cat requiere 'values' no vacío")


@dataclass(frozen=True)
class ComponentSpec:
    """Metadatos normalizados de un componente (bloque COMPONENT + la implementación)."""

    name: str
    slot: str
    compatible_skeletons: tuple[str, ...]
    requires: tuple[str, ...]
    params: dict[str, dict[str, Any]]
    impl: Any = field(compare=False, repr=False)

    @staticmethod
    def from_dict(component_dict: dict[str, Any], impl: Any) -> "ComponentSpec":
        missing = {"name", "slot"} - component_dict.keys()
        if missing:
            raise ComponentSpecError(f"COMPONENT no declara campos obligatorios: {missing}")

        slot = component_dict["slot"]
        if slot not in KNOWN_SLOTS:
            raise ComponentSpecError(
                f"slot '{slot}' desconocido; esperado uno de {sorted(KNOWN_SLOTS)}"
            )

        params = component_dict.get("params", {})
        if not isinstance(params, dict):
            raise ComponentSpecError("'params' debe ser un dict de nombre -> especificación")
        for pname, pspec in params.items():
            _validate_param(pname, pspec)

        compatible = tuple(component_dict.get("compatible_skeletons", ()))
        requires = tuple(component_dict.get("requires", ()))

        return ComponentSpec(
            name=component_dict["name"],
            slot=slot,
            compatible_skeletons=compatible,
            requires=requires,
            params=params,
            impl=impl,
        )

    def is_compatible_with(self, skeleton_name: str) -> bool:
        # Lista vacía == "sin restricción declarada" (compatible con cualquiera).
        return not self.compatible_skeletons or skeleton_name in self.compatible_skeletons

    def make(self, problem: Any, **params: Any):
        """Instancia el componente para `problem` con los parámetros dados.

        Convención de ensamblaje: `impl` es una *fábrica* `impl(problem, **params)`
        (la misma `build_component` de los módulos generados por LLM). Solo se
        pasan los parámetros declarados en `COMPONENT["params"]`; los demás se
        ignoran, así una configuración completa del tuner puede pasarse tal cual.
        """
        if not callable(self.impl):
            raise ComponentSpecError(f"el componente '{self.name}' no es una fábrica invocable")
        accepted = {k: v for k, v in params.items() if k in self.params}
        return self.impl(problem, **accepted)

    def default_params(self) -> dict[str, Any]:
        """Un valor razonable por parámetro (punto medio del rango / primer valor)."""
        out: dict[str, Any] = {}
        for name, spec in self.params.items():
            t = spec["type"]
            if t == "int":
                lo, hi = spec["range"]
                out[name] = int(round((lo + hi) / 2))
            elif t == "float":
                lo, hi = spec["range"]
                out[name] = (lo * hi) ** 0.5 if spec.get("log") and lo > 0 else (lo + hi) / 2
            elif t == "cat":
                out[name] = spec["values"][0]
            elif t == "bool":
                out[name] = True
        return out


class ComponentRegistry:
    """Colección de `ComponentSpec` indexada por slot.

    Es lo que el ensamblador (§2, §8) recorre para construir variantes
    ejecutables y lo que `config_space` recorre para construir el
    espacio jerárquico de configuración.
    """

    def __init__(self) -> None:
        self._by_slot: dict[str, list[ComponentSpec]] = {slot: [] for slot in KNOWN_SLOTS}

    def register(self, spec: ComponentSpec) -> None:
        existing_names = {c.name for c in self._by_slot[spec.slot]}
        if spec.name in existing_names:
            raise ComponentSpecError(
                f"ya existe un componente '{spec.name}' registrado en el slot '{spec.slot}'"
            )
        self._by_slot[spec.slot].append(spec)

    def register_module(self, module: Any) -> ComponentSpec:
        """Registra un módulo que expone `COMPONENT` y una clase de implementación.

        Convención: el módulo define `COMPONENT` (dict) y una clase
        cuyo nombre es `COMPONENT["name"]` en CamelCase, o expone
        directamente `IMPL` apuntando a la clase/instancia a usar.
        """
        if not hasattr(module, "COMPONENT"):
            raise ComponentSpecError(f"el módulo {module!r} no expone 'COMPONENT'")
        impl = getattr(module, "IMPL", None)
        if impl is None:
            raise ComponentSpecError(
                f"el módulo {module!r} no expone 'IMPL' (la clase/instancia del componente)"
            )
        spec = ComponentSpec.from_dict(module.COMPONENT, impl)
        self.register(spec)
        return spec

    def for_slot(self, slot: str) -> list[ComponentSpec]:
        if slot not in KNOWN_SLOTS:
            raise ComponentSpecError(f"slot '{slot}' desconocido")
        return list(self._by_slot[slot])

    def compatible(self, slot: str, skeleton_name: str) -> list[ComponentSpec]:
        return [c for c in self.for_slot(slot) if c.is_compatible_with(skeleton_name)]

    def get(self, slot: str, name: str) -> ComponentSpec:
        for c in self.for_slot(slot):
            if c.name == name:
                return c
        raise KeyError(f"no hay componente '{name}' registrado en el slot '{slot}'")

    def all_specs(self) -> Iterable[ComponentSpec]:
        for slot in KNOWN_SLOTS:
            yield from self._by_slot[slot]
