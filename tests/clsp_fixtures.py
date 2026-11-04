"""Componentes escritos a mano para el CLSP, sobre el modelo por piezas de referencia (`PartsModel` de
`examples.lotsizing.model_parts`): piezas conocidas (correctas) para probar las capas de validación, los esqueletos de
Python y el ensamblador sin depender del LLM ni de g++."""

from __future__ import annotations

from random import Random

from core.component import ComponentRegistry, ComponentSpec
from core.model_parts import PartsModel
from core.packs import GroupWindowDestruction, RandomVariableDestruction
from examples.lotsizing import model_parts
from examples.lotsizing.construction import EPS, CLSPPartial, CoverAction
from examples.lotsizing.instance import CLSPInstance

SKELETONS = ["SA", "ILS", "TS", "VNS", "HYB"]


def LotSizingModel(inst: CLSPInstance) -> PartsModel:
    return PartsModel(model_parts, inst)


class LotForLotConstructor:
    """Setup en cada período con demanda positiva (sin inventario)."""

    def build(self, inst: CLSPInstance, rng: Random):
        return tuple(tuple(d > 0 for d in row) for row in inst.demand)


class SetupFlipNeighborhood:
    """Invierte un setup y[i][t]."""

    def __init__(self, problem):
        self.problem = problem

    def moves(self, sol):
        for i in range(len(sol)):
            for t in range(len(sol[i])):
                yield (i, t)

    def apply(self, sol, m):
        i, t = m
        row = sol[i][:t] + (not sol[i][t],) + sol[i][t + 1:]
        return sol[:i] + (row,) + sol[i + 1:]

    def undo(self, sol, m):
        return self.apply(sol, m)  # el flip es su propia inversa

    def delta(self, sol, m) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


class SetupFlipPerturbation:
    def perturb(self, sol, strength: float, rng: Random):
        rows = [list(r) for r in sol]
        n_i, n_t = len(rows), len(rows[0])
        for _ in range(max(1, int(round(strength)))):
            i, t = rng.randrange(n_i), rng.randrange(n_t)
            rows[i][t] = not rows[i][t]
        return tuple(tuple(r) for r in rows)


COMPONENT_LOT_FOR_LOT = {"name": "lot_for_lot", "slot": "constructor", "compatible_skeletons": SKELETONS, "params": {}}
COMPONENT_SETUP_FLIP = {"name": "setup_flip", "slot": "neighborhood", "compatible_skeletons": SKELETONS, "params": {}}
COMPONENT_SETUP_FLIP_PERTURBATION = {"name": "setup_flip_perturbation", "slot": "perturbation",
                                     "compatible_skeletons": ["ILS", "HYB"], "params": {}}
COMPONENT_PERIOD_WINDOW = {"name": "period_window", "slot": "destruction", "compatible_skeletons": ["HYB"], "params": {}}


class UnitMarginalCost:
    """Puntaje de referencia: costo marginal por unidad cubierta (setup nuevo + inventario
    de llevar la producción de `source` a `period`)."""

    def __init__(self, problem):
        self.inst = problem.inst

    def score(self, p: CLSPPartial, a: CoverAction) -> float:
        inst = self.inst
        cost = (inst.setup_cost[a.item] if a.new_setup else 0.0) + inst.holding_cost[a.item] * (a.period - a.source) * a.qty
        return cost / max(a.qty, EPS)


class LatestSource:
    """Puntaje de referencia: producir lo más tarde posible (lot-for-lot cuando cabe)."""

    def __init__(self, problem):
        pass

    def score(self, p: CLSPPartial, a: CoverAction) -> float:
        return float(a.period - a.source)


COMPONENTS = [
    (COMPONENT_LOT_FOR_LOT, lambda problem: LotForLotConstructor()),
    ({"name": "unit_marginal_cost", "slot": "greedy_score", "compatible_skeletons": SKELETONS, "params": {}}, UnitMarginalCost),
    ({"name": "latest_source", "slot": "greedy_score", "compatible_skeletons": SKELETONS, "params": {}}, LatestSource),
    (COMPONENT_SETUP_FLIP, SetupFlipNeighborhood),
    (COMPONENT_SETUP_FLIP_PERTURBATION, lambda problem: SetupFlipPerturbation()),
    (COMPONENT_PERIOD_WINDOW, GroupWindowDestruction),
    ({"name": "random_setups", "slot": "destruction", "compatible_skeletons": ["HYB"], "params": {}}, RandomVariableDestruction),
]


def clsp_pack():
    """El pack del CLSP con este catálogo en lugar de las partidas genéricas."""
    from dataclasses import replace

    from examples.lotsizing.pack import PACK

    return replace(PACK, base_components=COMPONENTS, constructor_skeletons=SKELETONS)


def clsp_registry(exclude_slots: set[str] | None = None) -> ComponentRegistry:
    from core.catalog import build_registry

    return build_registry(clsp_pack(), exclude_slots)


__all__ = ["COMPONENT_LOT_FOR_LOT", "COMPONENT_PERIOD_WINDOW", "COMPONENT_SETUP_FLIP", "COMPONENT_SETUP_FLIP_PERTURBATION",
           "ComponentSpec", "COMPONENTS", "LatestSource", "LotForLotConstructor", "LotSizingModel", "SetupFlipNeighborhood",
           "SetupFlipPerturbation", "UnitMarginalCost", "clsp_pack", "clsp_registry"]
