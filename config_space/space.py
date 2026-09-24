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

from dataclasses import dataclass, field, replace
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
    # clave en la configuración final, si difiere de `name` (ver `ConfigSpace.fold`)
    key: str | None = None

    @property
    def config_key(self) -> str:
        return self.key or self.name

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

    def fold(self, assignment: dict[str, Any]) -> dict[str, Any]:
        """Asignación por nombre de nodo → configuración para el ensamblador: los nodos con
        `key` (un slot partido por grupo de esqueletos) vuelven a su clave común."""
        by_name = {n.name: n for n in self.nodes}
        return {(by_name[k].config_key if k in by_name else k): v for k, v in assignment.items()}


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
        # Esqueletos agrupados por el conjunto de componentes compatibles. Si todos comparten
        # el mismo, un único parámetro `slot` (lo usual). Si no (la validación por combinación
        # poda `compatible_skeletons` por componente), un parámetro por grupo, con
        # `key=slot`: con uno solo, el tuner podía elegir un componente incompatible con el
        # esqueleto muestreado y la variante fallaba (runs 9–14: hasta 5 de 40 trials).
        groups: dict[tuple[str, ...], list[str]] = {}
        for skel in skeletons:
            names = tuple(c.name for c in registry.compatible(slot, skel))
            if names:
                groups.setdefault(names, []).append(skel)
        split = len(groups) > 1
        for names, group in groups.items():
            suffix = f"__{'_'.join(group)}" if split else ""
            node_name = slot + suffix
            slot_condition = Condition(parent="skeleton", kind="in", values=tuple(group))
            space.add(
                ParamNode(
                    name=node_name,
                    type="cat",
                    values=names,
                    conditions=(slot_condition,),
                    key=slot if split else None,
                )
            )
            for comp in (registry.get(slot, n) for n in names):
                comp_condition = Condition(parent=node_name, kind="eq", values=(comp.name,))
                for pname, pspec in comp.params.items():
                    full_name = f"{comp.name}.{pname}"
                    node = _param_node_from_spec(full_name + suffix, pspec, conditions=(slot_condition, comp_condition))
                    space.add(replace(node, key=full_name) if split else node)

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
