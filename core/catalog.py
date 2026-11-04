"""Catálogo de componentes de un problema en la convención del `Assembler` (`impl(problem, **params)`): los del
`ProblemPack` (las partidas trivial y al azar, las destrucciones de Python del sub-MIP) más el vecindario compuesto y
los constructores greedy. Los componentes C++ generados entran por `llm.native_generator.load_native_catalog`."""

from __future__ import annotations

from core.component import ComponentRegistry, ComponentSpec
from core.construction import RULES, GreedyConstructor
from core.problem_pack import ProblemPack


def build_registry(pack: ProblemPack, exclude_slots: set[str] | None = None) -> ComponentRegistry:
    """Los componentes del pack; cada `greedy_score` se envuelve además como constructor `greedy_<nombre>`
    (`GreedyConstructor` con ese puntaje, con la regla y α como parámetros del tuner), y si hay dos o más vecindarios,
    `composite` con todos."""
    registry = ComponentRegistry()
    for component, factory in pack.handwritten:
        if exclude_slots and component["slot"] in exclude_slots:
            continue
        registry.register(ComponentSpec.from_dict(component, factory))
    for spec in list(registry.for_slot("greedy_score")):
        registry.register(greedy_constructor_spec(spec, pack.constructor_skeletons))
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


def greedy_constructor_spec(score_spec: ComponentSpec, skeletons: list[str]) -> ComponentSpec:
    params = {"rule": {"type": "cat", "values": list(RULES)}, "alpha": {"type": "float", "range": [0.0, 1.0]}}
    params.update(score_spec.params)

    def factory(problem, rule="greedy", alpha=0.2, **score_params):
        return GreedyConstructor(problem, score_spec.make(problem, **score_params), rule=rule, alpha=alpha)

    component = {"name": f"greedy_{score_spec.name}", "slot": "constructor",
                 "compatible_skeletons": list(score_spec.compatible_skeletons) or list(skeletons), "params": params}
    return ComponentSpec.from_dict(component, factory)
