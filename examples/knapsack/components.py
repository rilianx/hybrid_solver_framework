"""Componentes de ejemplo para knapsack 0/1 — el tipo de módulo que en el
sistema real generaría el LLM (§6 de la propuesta).

Cada clase implementa un `Protocol` de `core.contracts` y va acompañada
de su bloque `COMPONENT` + `IMPL`, siguiendo la convención de
`ComponentRegistry.register_module` (§4). Sirven para:

1. Ejercitar el núcleo end-to-end (`examples/knapsack/demo.py`).
2. Ser el ejemplo few-shot que se le mostraría al LLM al pedirle
   componentes para un problema nuevo.
"""

from __future__ import annotations

from random import Random


from .problem_model import KnapsackInstance, KnapsackModel, KnapsackObjective, Solution

# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


class GreedyRandomizedConstructor:
    """GRASP-style: construye ordenando por ratio valor/peso con una lista
    restringida de candidatos (RCL) de tamaño relativo `alpha`."""

    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha

    def build(self, inst: KnapsackInstance, rng: Random) -> Solution:
        remaining_capacity = inst.capacity
        taken = [False] * inst.n
        candidates = list(range(inst.n))
        while candidates:
            candidates = [i for i in candidates if inst.weights[i] <= remaining_capacity]
            if not candidates:
                break
            candidates.sort(key=lambda i: inst.values[i] / inst.weights[i], reverse=True)
            rcl_size = max(1, int(len(candidates) * self.alpha))
            choice = rng.choice(candidates[:rcl_size])
            taken[choice] = True
            remaining_capacity -= inst.weights[choice]
            candidates.remove(choice)
        return tuple(taken)


COMPONENT_GREEDY_RANDOMIZED_CONSTRUCTOR = {
    "name": "greedy_randomized_constructor",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "LNS_MIP"],
    "requires": [],
    "params": {"alpha": {"type": "float", "range": [0.05, 1.0]}},
}
COMPONENT = COMPONENT_GREEDY_RANDOMIZED_CONSTRUCTOR
IMPL = GreedyRandomizedConstructor


# ---------------------------------------------------------------------------
# Neighborhood + Evaluator (bit-flip)
# ---------------------------------------------------------------------------


class BitFlipNeighborhood:
    """Vecindario de flips de un bit; `delta` usa el evaluador ligado a la instancia."""

    def __init__(self, evaluator: KnapsackObjective):
        self.evaluator = evaluator

    def moves(self, sol: Solution):
        for i in range(len(sol)):
            yield (i, not sol[i])

    def apply(self, sol: Solution, m) -> Solution:
        i, new_val = m
        return sol[:i] + (new_val,) + sol[i + 1 :]

    def undo(self, sol: Solution, m) -> Solution:
        i, new_val = m
        old_val = not new_val
        return sol[:i] + (old_val,) + sol[i + 1 :]

    def delta(self, sol: Solution, m) -> float:
        return self.evaluator.incremental(sol, m) - self.evaluator.full(sol)


COMPONENT_BIT_FLIP_NEIGHBORHOOD = {
    "name": "bit_flip",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


# ---------------------------------------------------------------------------
# Perturbation
# ---------------------------------------------------------------------------


class RandomFlipPerturbation:
    """Perturbación de ILS: invierte `strength` bits elegidos al azar."""

    def perturb(self, sol: Solution, strength: float, rng: Random) -> Solution:
        n = len(sol)
        k = max(1, min(n, int(round(strength))))
        idxs = rng.sample(range(n), k)
        sol_list = list(sol)
        for i in idxs:
            sol_list[i] = not sol_list[i]
        return tuple(sol_list)


COMPONENT_RANDOM_FLIP_PERTURBATION = {
    "name": "random_flip",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "int", "range": [1, 10]}},
}


# ---------------------------------------------------------------------------
# Destruction
# ---------------------------------------------------------------------------


class RandomDestruction:
    """Libera una fracción `ratio` de los ítems, elegidos al azar, como `free_vars`."""

    def destroy(self, sol: Solution, ratio: float, rng: Random):
        n = len(sol)
        k = max(1, int(round(ratio * n)))
        free_idx = rng.sample(range(n), k)
        free_vars = {f"x{i}" for i in free_idx}
        partial = {f"x{i}": (1.0 if sol[i] else 0.0) for i in range(n) if i not in free_idx}
        return partial, free_vars


COMPONENT_RANDOM_DESTRUCTION = {
    "name": "random_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": [],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class RelatedDestruction:
    """Libera los `ratio` ítems con peor ratio valor/peso dentro de la solución actual
    (más "relacionados" con una mala decisión de empaquetado que un ítem al azar)."""

    def __init__(self, inst: KnapsackInstance):
        self.inst = inst

    def destroy(self, sol: Solution, ratio: float, rng: Random):
        n = len(sol)
        taken_idx = [i for i in range(n) if sol[i]]
        k = max(1, min(len(taken_idx), int(round(ratio * n))))
        taken_idx.sort(key=lambda i: self.inst.values[i] / self.inst.weights[i])
        free_idx = set(taken_idx[:k])
        free_vars = {f"x{i}" for i in free_idx}
        partial = {f"x{i}": (1.0 if sol[i] else 0.0) for i in range(n) if i not in free_idx}
        return partial, free_vars


COMPONENT_RELATED_DESTRUCTION = {
    "name": "related_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["KnapsackInstance"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


# ---------------------------------------------------------------------------
# Repair MIP
# ---------------------------------------------------------------------------


class KnapsackMIPRepair:
    """Reparación MIP (slot `repair_mip`): delega en `KnapsackMip.solve` liberando
    `free_vars` como enteras y fijando el resto; equivale al genérico
    `core.common_components.MIPModelRepair` pero se mantiene como ejemplo few-shot."""

    def __init__(self, base_model: KnapsackModel | None = None):
        self.base_model = base_model or KnapsackModel()

    def repair_mip(
        self,
        model,
        fixed: dict[str, float],
        free_vars: set[str],
        time_limit: float,
        warm_start: dict[str, float] | None = None,
    ) -> Solution | None:
        x = model.solve(fixed=fixed, integer=set(free_vars), relaxed=set(), time_limit=time_limit, warm_start=warm_start)
        return None if x is None else self.base_model.from_assignment(x)


COMPONENT_KNAPSACK_MIP_REPAIR = {
    "name": "knapsack_mip_repair",
    "slot": "repair_mip",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["pulp"],
    "params": {"mip_time_limit": {"type": "float", "range": [0.5, 10.0], "log": True}},
}


def build_registry(inst: KnapsackInstance, evaluator: KnapsackObjective):
    """Registra los componentes de este módulo, ya ligados a `inst`/`evaluator`
    cuando lo necesitan, en un `core.component.ComponentRegistry` nuevo."""
    from core.component import ComponentRegistry, ComponentSpec

    registry = ComponentRegistry()
    registry.register(ComponentSpec.from_dict(COMPONENT_GREEDY_RANDOMIZED_CONSTRUCTOR, GreedyRandomizedConstructor))
    registry.register(
        ComponentSpec.from_dict(COMPONENT_BIT_FLIP_NEIGHBORHOOD, BitFlipNeighborhood(evaluator))
    )
    registry.register(ComponentSpec.from_dict(COMPONENT_RANDOM_FLIP_PERTURBATION, RandomFlipPerturbation))
    registry.register(ComponentSpec.from_dict(COMPONENT_RANDOM_DESTRUCTION, RandomDestruction))
    registry.register(ComponentSpec.from_dict(COMPONENT_RELATED_DESTRUCTION, RelatedDestruction(inst)))
    registry.register(ComponentSpec.from_dict(COMPONENT_KNAPSACK_MIP_REPAIR, KnapsackMIPRepair()))
    return registry
