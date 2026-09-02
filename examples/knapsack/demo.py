"""Demo end-to-end del núcleo sobre knapsack 0/1.

Ejecuta las tres especializaciones del esqueleto genérico (SA, ILS,
LNS-MIP) sobre la misma instancia, y exporta el espacio de
configuración compuesto a irace y a un `optuna.trial` de prueba.
Uso: `python -m examples.knapsack.demo` desde la raíz del repo.
"""

from __future__ import annotations

from random import Random

from core.common_components import (
    AlwaysAccept,
    BetterAcceptance,
    MaxIterationsStop,
)
from config_space import build_config_space, to_irace_parameters, suggest_from_space
from skeletons.ils import build_ils, hill_climb
from skeletons.lns_mip import build_lns_mip, run_lns_mip
from skeletons.sa import build_sa, make_run

from .components import (
    BitFlipNeighborhood,
    GreedyRandomizedConstructor,
    KnapsackMIPRepair,
    RandomDestruction,
    RandomFlipPerturbation,
    build_registry,
)
from .problem_model import KnapsackInstance, KnapsackModel, KnapsackObjective, bound_problem_model


def run_demo(n: int = 30, seed: int = 42, max_iterations: int = 200) -> None:
    rng = Random(seed)
    inst = KnapsackInstance.random(n, rng)

    base_model = KnapsackModel()
    evaluator = KnapsackObjective(base_model, inst)
    problem = bound_problem_model(inst)

    constructor = GreedyRandomizedConstructor(alpha=0.3)
    neighborhood = BitFlipNeighborhood(evaluator)
    stop = MaxIterationsStop(max_iterations)

    print(f"Instancia: n={n}, capacity={inst.capacity:.1f}")

    # --- SA ---
    sa_skeleton, sa_extra = build_sa(problem, constructor, neighborhood, stop, T0=5.0, alpha=0.95)
    sa_run = make_run(sa_skeleton, sa_extra)
    sa_result = sa_run(inst, Random(seed))
    print(f"SA:      valor={-sa_result.best_objective:.2f}  iters={sa_result.iterations}")

    # --- ILS ---
    ls = hill_climb(problem, neighborhood, strategy="best")
    perturbation = RandomFlipPerturbation()
    ils_skeleton = build_ils(
        problem, constructor, ls, perturbation, BetterAcceptance(), MaxIterationsStop(max_iterations // 5)
    )
    ils_result = ils_skeleton.run(inst, Random(seed))
    print(f"ILS:     valor={-ils_result.best_objective:.2f}  iters={ils_result.iterations}")

    # --- LNS-MIP ---
    destruction = RandomDestruction()
    repair_mip = KnapsackMIPRepair(base_model)
    lns_skeleton = build_lns_mip(
        problem,
        constructor,
        destruction,
        repair_mip,
        AlwaysAccept(),
        MaxIterationsStop(max(5, max_iterations // 20)),
        destroy_ratio=0.3,
        mip_time_limit=1.0,
    )
    lns_result = run_lns_mip(lns_skeleton, inst, Random(seed), destroy_ratio=0.3)
    print(f"LNS-MIP: valor={-lns_result.best_objective:.2f}  iters={lns_result.iterations}")

    # --- Espacio de configuración compuesto (§8) ---
    registry = build_registry(inst, evaluator)
    space = build_config_space(
        registry,
        skeleton_names=["SA", "ILS", "LNS_MIP"],
        slots_per_skeleton={
            "SA": ["constructor", "neighborhood"],
            "ILS": ["constructor", "neighborhood", "perturbation"],
            "LNS_MIP": ["constructor", "destruction", "repair_mip"],
        },
        skeleton_params={
            "SA": {
                "T0": {"type": "float", "range": [0.1, 100], "log": True},
                "alpha": {"type": "float", "range": [0.8, 0.999]},
            },
            "LNS_MIP": {
                "mip_time_limit": {"type": "float", "range": [0.5, 30], "log": True},
            },
        },
    )
    print("\n--- parameters.txt (irace) ---")
    print(to_irace_parameters(space))

    class _FakeTrial:
        def __init__(self, rng: Random):
            self.rng = rng
            self.params: dict = {}

        def suggest_int(self, name, low, high, *, log=False):
            v = self.rng.randint(low, high)
            self.params[name] = v
            return v

        def suggest_float(self, name, low, high, *, log=False):
            v = self.rng.uniform(low, high)
            self.params[name] = v
            return v

        def suggest_categorical(self, name, choices):
            v = self.rng.choice(choices)
            self.params[name] = v
            return v

    trial = _FakeTrial(Random(seed))
    assignment = suggest_from_space(space, trial)
    print("--- muestra Optuna define-by-run ---")
    for k, v in assignment.items():
        print(f"  {k} = {v}")


if __name__ == "__main__":
    run_demo()
