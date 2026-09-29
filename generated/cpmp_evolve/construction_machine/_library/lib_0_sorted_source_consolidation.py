COMPONENT = {
    "name": "sacrifice_sorted_source_to_consolidate",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {
        "min_source_height": {"type": "int", "range": [1, 10], "default": 1},
        "max_source_height": {"type": "int", "range": [1, 10], "default": 2},
    },
}

from core.rules import RuleMachine


class SortedSourceConsolidationRule:
    """Permite mover la cima de una pila fuente ya ordenada y baja a otra pila ordenada, aun desordenándola, para consolidar y liberar la fuente."""

    name = "sorted_source_consolidation"

    def __init__(self, min_source_height: int, max_source_height: int):
        self.min_source_height = min_source_height
        self.max_source_height = max_source_height

    def allowed(self, partial, memory, candidates):
        actions = []
        for action in candidates:
            source_height = partial.h(action.so)
            if source_height < self.min_source_height or source_height > self.max_source_height:
                continue
            if not partial.is_sorted_stack(action.so):
                continue
            if not partial.is_sorted_stack(action.sd):
                continue
            moved_group = partial.g(action.so)
            destination_top = partial.g(action.sd)
            if moved_group <= destination_top:
                continue
            actions.append(action)

        return sorted(
            actions,
            key=lambda action: (
                partial.h(action.so),
                -partial.g(action.so),
                partial.h(action.sd),
                action.so,
                action.sd,
            ),
        )


def build_component(problem, min_source_height=1, max_source_height=2, **params):
    rule = SortedSourceConsolidationRule(
        min_source_height=min_source_height,
        max_source_height=max_source_height,
    )
    return RuleMachine(problem, [rule])
