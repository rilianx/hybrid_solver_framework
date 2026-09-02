"""Espacio de diseño jerárquico (§8 de la propuesta).

Construye, a partir del `ComponentRegistry` y de la declaración de qué
slots usa cada esqueleto, un espacio de parámetros condicional:

    skeleton      ∈ {SA, ILS, LNS_MIP}                              (raíz)
    neighborhood  ∈ {two_opt, or_opt, swap}   | skeleton ∈ {SA, ILS}
    two_opt.sample_size ∈ [10, 500] log       | neighborhood == "two_opt"
    SA.T0 ∈ [0.1, 100] log                    | skeleton == "SA"

Este `ConfigSpace` es intencionalmente neutro respecto al tuner: los
exportadores en `irace_export.py` y `optuna_export.py` lo traducen a
`parameters.txt` y a un espacio *define-by-run*, respectivamente,
como pide la sección 8.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.component import ComponentRegistry


@dataclass(frozen=True)
class Condition:
    """Condición de activación de un parámetro, en forma normalizada.

    `kind` es "in" (el parent debe tomar uno de `values`) o "eq"
    (el parent debe ser exactamente `values[0]`). Mantenerlo
    estructurado (en vez de un string) es lo que permite traducirlo
    sin ambigüedad a cada tuner.
    """

    parent: str
    kind: str  # "in" | "eq"
    values: tuple[Any, ...]

    def as_irace_expr(self) -> str:
        def _fmt(v: Any) -> str:
            return f'"{v}"' if isinstance(v, str) else str(v)

        if self.kind == "eq":
            return f"{self.parent} == {_fmt(self.values[0])}"
        joined = ", ".join(_fmt(v) for v in self.values)
        return f"{self.parent} %in% c({joined})"

    def holds(self, assignment: dict[str, Any]) -> bool:
        if self.parent not in assignment:
            return False
        if self.kind == "eq":
            return assignment[self.parent] == self.values[0]
        return assignment[self.parent] in self.values


@dataclass(frozen=True)
class ParamNode:
    name: str
    type: str  # "int" | "float" | "cat" | "bool"
    values: tuple[Any, ...] | None = None  # para "cat"/"bool"
    range: tuple[float, float] | None = None  # para "int"/"float"
    log: bool = False
    conditions: tuple[Condition, ...] = field(default_factory=tuple)

    def is_active(self, assignment: dict[str, Any]) -> bool:
        return all(c.holds(assignment) for c in self.conditions)


class ConfigSpace:
    def __init__(self) -> None:
        self.nodes: list[ParamNode] = []

    def add(self, node: ParamNode) -> None:
        if any(n.name == node.name for n in self.nodes):
            raise ValueError(f"parámetro duplicado en el espacio: '{node.name}'")
        self.nodes.append(node)

    def roots(self) -> list[ParamNode]:
        return [n for n in self.nodes if not n.conditions]

    def children_of(self, name: str) -> list[ParamNode]:
        return [n for n in self.nodes if any(c.parent == name for c in n.conditions)]

    def active_nodes(self, assignment: dict[str, Any]) -> list[ParamNode]:
        return [n for n in self.nodes if n.is_active(assignment)]


def build_config_space(
    registry: ComponentRegistry,
    skeleton_names: list[str],
    slots_per_skeleton: dict[str, list[str]],
    skeleton_params: dict[str, dict[str, dict[str, Any]]] | None = None,
) -> ConfigSpace:
    """Construye el `ConfigSpace` completo: raíz `skeleton` + slots + params por componente.

    `slots_per_skeleton`: qué slots usa cada esqueleto, p.ej.
        {"SA": ["constructor", "neighborhood"], "LNS_MIP": ["constructor", "destruction", "repair_mip"]}

    `skeleton_params`: parámetros propios del esqueleto (no de un
    componente), condicionados solo a `skeleton == <nombre>`, p.ej.
        {"SA": {"T0": {"type": "float", "range": [0.1, 100], "log": True}, ...}}
    """
    space = ConfigSpace()
    space.add(ParamNode(name="skeleton", type="cat", values=tuple(skeleton_names)))

    # Slot -> lista de esqueletos que lo usan, para agrupar en un único
    # parámetro categórico por slot (§8: "neighborhood ... | skeleton ∈ {SA, TS, ILS}").
    skeletons_using_slot: dict[str, list[str]] = {}
    for skel, slots in slots_per_skeleton.items():
        for slot in slots:
            skeletons_using_slot.setdefault(slot, []).append(skel)

    for slot, skeletons in skeletons_using_slot.items():
        components = [
            c
            for skel in skeletons
            for c in registry.compatible(slot, skel)
        ]
        # de-duplicar preservando orden
        seen = set()
        unique = []
        for c in components:
            if c.name not in seen:
                seen.add(c.name)
                unique.append(c)
        if not unique:
            continue

        slot_condition = Condition(parent="skeleton", kind="in", values=tuple(skeletons))
        space.add(
            ParamNode(
                name=slot,
                type="cat",
                values=tuple(c.name for c in unique),
                conditions=(slot_condition,),
            )
        )

        for comp in unique:
            comp_condition = Condition(parent=slot, kind="eq", values=(comp.name,))
            for pname, pspec in comp.params.items():
                full_name = f"{comp.name}.{pname}"
                space.add(_param_node_from_spec(full_name, pspec, conditions=(slot_condition, comp_condition)))

    for skel, params in (skeleton_params or {}).items():
        skel_condition = Condition(parent="skeleton", kind="eq", values=(skel,))
        for pname, pspec in params.items():
            full_name = f"{skel}.{pname}"
            space.add(_param_node_from_spec(full_name, pspec, conditions=(skel_condition,)))

    return space


def _param_node_from_spec(name: str, pspec: dict[str, Any], conditions: tuple[Condition, ...]) -> ParamNode:
    ptype = pspec["type"]
    if ptype in ("int", "float"):
        lo, hi = pspec["range"]
        return ParamNode(
            name=name,
            type=ptype,
            range=(lo, hi),
            log=bool(pspec.get("log", False)),
            conditions=conditions,
        )
    if ptype == "cat":
        return ParamNode(name=name, type="cat", values=tuple(pspec["values"]), conditions=conditions)
    if ptype == "bool":
        return ParamNode(name=name, type="bool", values=(True, False), conditions=conditions)
    raise ValueError(f"tipo de parámetro no soportado: {ptype}")
