"""Catálogo de componentes de un problema en la convención del `Assembler` (`impl(problem, **params)`): los del
`ProblemPack` (las partidas trivial y al azar, las destrucciones de Python del sub-MIP) más el vecindario compuesto. Los componentes C++ generados entran por `llm.native_generator.load_native_catalog`."""

from __future__ import annotations

from core.component import ComponentRegistry, ComponentSpec
from core.problem_pack import ProblemPack


def build_registry(pack: ProblemPack, exclude_slots: set[str] | None = None) -> ComponentRegistry:
    """Los componentes del pack y, si hay dos o más vecindarios, `composite` con todos."""
    registry = ComponentRegistry()
    for component, factory in pack.base_components:
        if exclude_slots and component["slot"] in exclude_slots:
            continue
        registry.register(ComponentSpec.from_dict(component, factory))
    composite = composite_spec(registry.for_slot("neighborhood"))
    if composite is not None:
        registry.register(composite)
    return registry


COMPOSITE = "composite"


def composite_spec(nbhs: list[ComponentSpec]) -> ComponentSpec | None:
    """`composite`: todos los vecindarios del catálogo a la vez (`core.neighborhood.CompositeNeighborhood`; en C++,
    `hsf::CompositeNeighborhood`), en los esqueletos que todos comparten. Cada vecindario con sus parámetros por
    defecto. Con menos de dos vecindarios no hay nada que unir."""
    from core.neighborhood import CompositeNeighborhood

    nbhs = [s for s in nbhs if s.name != COMPOSITE]
    if len(nbhs) < 2:
        return None
    common = set(nbhs[0].compatible_skeletons)
    for s in nbhs[1:]:
        common &= set(s.compatible_skeletons)
    skeletons = [k for k in nbhs[0].compatible_skeletons if k in common]
    if not skeletons:
        return None
    return ComponentSpec.from_dict({"name": COMPOSITE, "slot": "neighborhood", "compatible_skeletons": skeletons, "params": {}},
                                   lambda problem: CompositeNeighborhood([s.make(problem) for s in nbhs]))
