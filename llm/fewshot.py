"""Ejemplos few-shot por slot (§6): componentes válidos para un problema
*distinto* al que se está generando (knapsack 0/1), escritos en la
convención de módulo generado:

    COMPONENT = {...}                       # bloque de metadatos (§4)
    class X: ...                            # implementa el Protocol del slot
    def build_component(problem, **params): # fábrica: recibe el ProblemModel ya
        return X(...)                       # ligado a la instancia, y los params
                                            # con los valores por defecto del tuner

La fábrica es lo que permite que el componente reciba lo que necesite
(instancia, evaluador) sin que el núcleo conozca su constructor.
"""

FEWSHOT: dict[str, str] = {}

FEWSHOT["constructor"] = '''
from random import Random

COMPONENT = {
    "name": "greedy_ratio_rcl",
    "slot": "constructor",
    "compatible_skeletons": ["SA", "ILS", "LNS_MIP"],
    "requires": [],
    "params": {"alpha": {"type": "float", "range": [0.05, 1.0]}},
}


class GreedyRatioRCL:
    """GRASP: ordena por valor/peso y elige al azar dentro de una lista restringida de tamaño alpha."""

    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha

    def build(self, inst, rng: Random):
        remaining, taken = inst.capacity, [False] * inst.n
        candidates = list(range(inst.n))
        while candidates:
            candidates = [i for i in candidates if inst.weights[i] <= remaining]
            if not candidates:
                break
            candidates.sort(key=lambda i: inst.values[i] / inst.weights[i], reverse=True)
            choice = rng.choice(candidates[: max(1, int(len(candidates) * self.alpha))])
            taken[choice] = True
            remaining -= inst.weights[choice]
            candidates.remove(choice)
        return tuple(taken)


def build_component(problem, alpha: float = 0.3):
    return GreedyRatioRCL(alpha=alpha)
'''

FEWSHOT["neighborhood"] = '''
COMPONENT = {
    "name": "swap_in_out",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS"],
    "requires": ["ProblemModel.objective"],
    "params": {},
}


class SwapInOut:
    """Intercambia un ítem dentro de la mochila por uno fuera. Movimiento = (i_out, i_in)."""

    def __init__(self, problem):
        self.problem = problem  # objective(sol) ya ligado a la instancia

    def moves(self, sol):
        inside = [i for i, t in enumerate(sol) if t]
        outside = [i for i, t in enumerate(sol) if not t]
        for i in inside:
            for j in outside:
                yield (i, j)

    def apply(self, sol, m):
        i, j = m
        s = list(sol)
        s[i], s[j] = False, True
        return tuple(s)

    def undo(self, sol, m):
        i, j = m
        s = list(sol)
        s[i], s[j] = True, False
        return tuple(s)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol)


def build_component(problem):
    return SwapInOut(problem)
'''

FEWSHOT["perturbation"] = '''
from random import Random

COMPONENT = {
    "name": "random_flip_k",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "int", "range": [1, 10]}},
}


class RandomFlipK:
    def perturb(self, sol, strength: float, rng: Random):
        k = max(1, min(len(sol), int(round(strength))))
        s = list(sol)
        for i in rng.sample(range(len(sol)), k):
            s[i] = not s[i]
        return tuple(s)


def build_component(problem):
    return RandomFlipK()
'''

FEWSHOT["destruction"] = '''
from random import Random

COMPONENT = {
    "name": "worst_ratio_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {"ratio": {"type": "float", "range": [0.05, 0.6]}},
}


class WorstRatioDestruction:
    """Libera los ítems dentro de la mochila con peor valor/peso (+ algo de azar)."""

    def __init__(self, problem, inst):
        self.problem, self.inst = problem, inst

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)  # {"x0": 0/1, ...}
        n = len(sol)
        k = max(1, int(round(ratio * n)))
        inside = sorted((i for i in range(n) if sol[i]), key=lambda i: self.inst.values[i] / self.inst.weights[i])
        chosen = set(inside[:k])
        while len(chosen) < k:
            chosen.add(rng.randrange(n))
        free_vars = {f"x{i}" for i in chosen}
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem):
    return WorstRatioDestruction(problem, problem.inst)
'''
