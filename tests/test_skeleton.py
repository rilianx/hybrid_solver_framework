"""Prueba el esqueleto genérico y las tres especializaciones sobre un
problema de juguete minúsculo (minimizar (x - target)^2 sobre enteros),
independiente de knapsack, para aislar bugs del núcleo de bugs del
ejemplo de knapsack.
"""

from random import Random

from core.common_components import AlwaysAccept, BetterAcceptance, MaxIterationsStop
from skeletons.ils import build_ils, hill_climb
from skeletons.sa import build_sa, make_run

TARGET = 17
LO, HI = 0, 50


class ToyProblem:
    def objective(self, sol: int) -> float:
        return (sol - TARGET) ** 2

    def is_feasible(self, sol: int) -> bool:
        return LO <= sol <= HI


class ToyConstructor:
    def build(self, inst, rng: Random) -> int:
        return rng.randint(LO, HI)


class ToyNeighborhood:
    def __init__(self, problem: ToyProblem):
        self.problem = problem

    def moves(self, sol: int):
        if sol > LO:
            yield -1
        if sol < HI:
            yield 1

    def apply(self, sol: int, m: int) -> int:
        return sol + m

    def undo(self, sol: int, m: int) -> int:
        return sol - m

    def delta(self, sol: int, m: int) -> float:
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


class ToyPerturbation:
    def perturb(self, sol: int, strength: float, rng: Random) -> int:
        kick = rng.choice([-1, 1]) * max(1, int(strength))
        return max(LO, min(HI, sol + kick))


def test_generic_skeleton_hill_climb_reaches_optimum():
    problem = ToyProblem()
    neighborhood = ToyNeighborhood(problem)
    ls = hill_climb(problem, neighborhood, strategy="best")
    rng = Random(0)
    result = ls(25, rng)
    assert problem.objective(result) == 0


def test_sa_improves_over_random_and_is_deterministic_given_seed():
    problem = ToyProblem()
    neighborhood = ToyNeighborhood(problem)
    constructor = ToyConstructor()
    stop = MaxIterationsStop(300)

    skeleton, extra = build_sa(problem, constructor, neighborhood, stop, T0=5.0, alpha=0.9)
    run = make_run(skeleton, extra)

    result_a = run(None, Random(123))
    result_b = run(None, Random(123))

    assert result_a.best_objective == result_b.best_objective  # determinismo con semilla
    assert result_a.best_objective <= problem.objective(25)  # mejora sobre un punto arbitrario
    assert result_a.iterations == 300


def test_ils_with_hill_climb_inner_search_reaches_optimum():
    problem = ToyProblem()
    neighborhood = ToyNeighborhood(problem)
    constructor = ToyConstructor()
    ls = hill_climb(problem, neighborhood, strategy="best")
    perturbation = ToyPerturbation()
    stop = MaxIterationsStop(20)

    skeleton = build_ils(problem, constructor, ls, perturbation, BetterAcceptance(), stop)
    result = skeleton.run(None, Random(7))

    assert result.best_objective == 0
    assert result.iterations == 20


def test_always_accept_never_rejects():
    acc = AlwaysAccept()
    assert acc.accept(f_cur=10, f_cand=999, state=None) is True


def test_better_acceptance_rejects_worse():
    acc = BetterAcceptance()
    assert acc.accept(f_cur=10, f_cand=11, state=None) is False
    assert acc.accept(f_cur=10, f_cand=9, state=None) is True
