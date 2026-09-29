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

FEWSHOT["construction_policy"] = '''
COMPONENT = {
    "name": "fill_then_top_up",
    "slot": "construction_policy",
    "compatible_skeletons": ["SA", "ILS", "LNS_MIP"],
    "requires": [],
    "params": {"switch_slack": {"type": "float", "range": [0.05, 0.5]}},
}


class FillThenTopUp:
    """Mochila, en dos fases que recuerda la memoria: primero LLENAR con los ítems de mayor valor
    por unidad de peso; cuando la holgura cae bajo `switch_slack` de la capacidad, pasa a COMPLETAR
    con el ítem que mejor aprovecha lo que queda (el de mayor valor que cabe). La acción es
    `action.item`; el parcial expone `partial.remaining` (capacidad libre). Menor = mejor."""

    def __init__(self, problem, switch_slack: float = 0.2):
        self.inst = problem.inst
        self.threshold = switch_slack * problem.inst.capacity

    def init(self, partial):
        return ("fill",)  # memoria: la fase del plan (tupla: inmutable y hashable)

    def score(self, partial, memory, action):
        w, v = self.inst.weights[action.item], self.inst.values[action.item]
        if memory[0] == "fill":
            return -v / max(w, 1e-9)
        return -v + 1e-6 * (partial.remaining - w)

    def update(self, partial, memory, action):
        left = partial.remaining - self.inst.weights[action.item]
        return ("top_up",) if memory[0] == "fill" and left < self.threshold else memory


def build_component(problem, switch_slack: float = 0.2):
    return FillThenTopUp(problem, switch_slack)
'''

FEWSHOT["construction_machine"] = '''
COMPONENT = {
    "name": "category_then_top_up",
    "slot": "construction_machine",
    "compatible_skeletons": ["SA", "ILS", "LNS_MIP"],
    "requires": [],
    "params": {
        "min_fit": {"type": "int", "range": [1, 5], "default": 2},
        "top_up_slack": {"type": "float", "range": [0.05, 0.5], "default": 0.2},
    },
}

from core.rules import RuleMachine


class FillCategory:
    """Macro: al activarse elige la categoría de mayor valor por peso medio entre las que tienen al
    menos `min_fit` ítems que caben (`inst.category[i]`), y permite sus ítems (mayor valor por peso
    primero) hasta que no quepa ninguno. La acción es `action.item`; el parcial expone
    `partial.remaining` y `partial.chosen`."""

    name = "fill_category"
    priority = 100

    def __init__(self, inst, min_fit):
        self.inst, self.min_fit = inst, min_fit

    def _fitting(self, partial, cat):
        return [i for i, c in enumerate(self.inst.category) if c == cat and i not in partial.chosen
                and self.inst.weights[i] <= partial.remaining]

    def init(self, partial):
        return (None,)

    def start(self, partial, memory):
        cats = [c for c in sorted(set(self.inst.category)) if len(self._fitting(partial, c)) >= self.min_fit]
        def density(c):
            items = self._fitting(partial, c)
            return sum(self.inst.values[i] / max(self.inst.weights[i], 1e-9) for i in items) / len(items)
        return (max(cats, key=density) if cats else None,)

    def allowed(self, partial, memory, candidates):
        if memory[0] is None:
            return []
        mine = [a for a in candidates if self.inst.category[a.item] == memory[0]]
        return sorted(mine, key=lambda a: -self.inst.values[a.item] / max(self.inst.weights[a.item], 1e-9))

    def done(self, partial, memory):
        return memory[0] is None or not self._fitting(partial, memory[0])


class TopUp:
    """Regla simple: el ítem de mayor valor que todavía cabe. Prioridad menor que FillCategory:
    completa cuando no queda categoría que llenar."""

    name = "top_up"
    priority = 50

    def __init__(self, inst, top_up_slack):
        self.inst, self.threshold = inst, top_up_slack * inst.capacity

    def allowed(self, partial, memory, candidates):
        return sorted(candidates, key=lambda a: -self.inst.values[a.item])


class TopUpWhenTight(TopUp):
    """La misma regla, con prioridad sobre las demás cuando queda poca holgura."""

    name = "top_up_tight"
    priority = 200

    def allowed(self, partial, memory, candidates):
        return super().allowed(partial, memory, candidates) if partial.remaining < self.threshold else []


def build_component(problem, min_fit: int = 2, top_up_slack: float = 0.2):
    inst = problem.inst
    return RuleMachine(problem, [TopUpWhenTight(inst, top_up_slack), FillCategory(inst, min_fit), TopUp(inst, top_up_slack)])
'''

FEWSHOT["greedy_score"] = '''
COMPONENT = {
    "name": "value_density_with_slack",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "LNS_MIP"],
    "requires": [],
    "params": {"slack_weight": {"type": "float", "range": [0.0, 2.0]}},
}


class ValueDensityWithSlack:
    """Mochila: la acción es `action.item` (meter el ítem); el parcial expone `partial.remaining`
    (capacidad libre). Prefiere mayor valor por unidad de peso y penaliza dejar la mochila
    casi llena (poca holgura para lo que viene). Menor puntaje = mejor."""

    def __init__(self, problem, slack_weight: float = 0.5):
        self.inst = problem.inst
        self.slack_weight = slack_weight

    def score(self, partial, action):
        w, v = self.inst.weights[action.item], self.inst.values[action.item]
        density = v / max(w, 1e-9)
        left = partial.remaining - w
        return -density + self.slack_weight * (1.0 / (1.0 + left))


def build_component(problem, slack_weight: float = 0.5):
    return ValueDensityWithSlack(problem, slack_weight)
'''
