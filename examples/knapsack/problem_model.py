"""`ProblemModel` del problema piloto: mochila 0/1 (knapsack).

Se eligió knapsack en vez del *lot sizing* sugerido en el plan de
trabajo (§9.2) porque para validar el núcleo (Protocols + esqueleto +
exportadores) alcanza con el problema combinatorio más simple posible
que tenga a la vez una vista estructural natural (vector binario) y
una formulación MIP trivial de verificar a mano. El piloto real de
lot-sizing/scheduling queda para la fase 2 del plan (§9), una vez el
núcleo esté ejercitado end-to-end.

Convención de minimización: `objective()` retorna el valor total
**negado**, para que "menor es mejor" sea válido en todo el núcleo
(igual que en el pseudocódigo de la propuesta, que asume minimización).
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

Solution = tuple[bool, ...]


@dataclass(frozen=True)
class KnapsackInstance:
    weights: tuple[float, ...]
    values: tuple[float, ...]
    capacity: float

    @property
    def n(self) -> int:
        return len(self.weights)

    @staticmethod
    def random(n: int, rng: Random, capacity_ratio: float = 0.5) -> "KnapsackInstance":
        weights = tuple(rng.uniform(1, 20) for _ in range(n))
        values = tuple(rng.uniform(1, 20) for _ in range(n))
        capacity = capacity_ratio * sum(weights)
        return KnapsackInstance(weights=weights, values=values, capacity=capacity)


class KnapsackModel:
    """Implementa el `Protocol` `core.contracts.ProblemModel` para knapsack 0/1."""

    def load(self, path: str) -> KnapsackInstance:
        weights: list[float] = []
        values: list[float] = []
        capacity = 0.0
        with open(path) as f:
            capacity = float(f.readline())
            for line in f:
                if not line.strip():
                    continue
                w, v = line.split()
                weights.append(float(w))
                values.append(float(v))
        return KnapsackInstance(weights=tuple(weights), values=tuple(values), capacity=capacity)

    def total_weight(self, inst: KnapsackInstance, sol: Solution) -> float:
        return sum(w for w, taken in zip(inst.weights, sol) if taken)

    def is_feasible(self, sol: Solution, inst: KnapsackInstance | None = None) -> bool:
        if inst is None:
            raise ValueError("KnapsackModel.is_feasible requiere `inst` (firma extendida)")
        return self.total_weight(inst, sol) <= inst.capacity

    def objective(self, sol: Solution, inst: KnapsackInstance | None = None) -> float:
        # Convención de minimización del núcleo: negamos el valor total.
        # `inst` no forma parte del Protocol genérico (que solo ve `sol`),
        # pero aquí lo aceptamos opcionalmente para poder penalizar
        # infactibilidad sin que el llamador tenga que pasarlo siempre
        # (los componentes de este ejemplo siempre lo pasan).
        raise NotImplementedError  # ver KnapsackObjective más abajo

    def build_mip(self, inst: KnapsackInstance) -> "KnapsackMip":
        return KnapsackMip(inst)

    def to_assignment(self, sol: Solution) -> dict[str, float]:
        return {f"x{i}": 1.0 if taken else 0.0 for i, taken in enumerate(sol)}

    def from_assignment(self, x: dict[str, float]) -> Solution:
        n = len(x)
        return tuple(round(x[f"x{i}"]) >= 1 for i in range(n))

    def variable_groups(self, inst: KnapsackInstance) -> dict[str, list[str]]:
        # Sin estructura temporal/espacial real; una única bolsa de
        # variables. Suficiente para ejercitar Destrucción/Reparación MIP;
        # un piloto con estructura (lot sizing, scheduling) es lo que
        # justifica variable_groups no triviales (ventanas, bloques).
        return {"items": [f"x{i}" for i in range(inst.n)]}


class KnapsackMip:
    """`core.mip.MIPModel` para knapsack 0/1 (PuLP/CBC).

    Objetivo en convención de minimización (valor negado) para que
    coincida con `KnapsackObjective` y la capa semántica pueda compararlos.
    Se reconstruye el LP en cada `solve`: para knapsack es más barato que
    mantener un `LpProblem` vivo y evita acumular restricciones.
    """

    def __init__(self, inst: KnapsackInstance):
        self.inst = inst
        self.last_objective: float | None = None

    def variables(self) -> list[str]:
        return [f"x{i}" for i in range(self.inst.n)]

    def solve(self, fixed, integer, relaxed, time_limit, warm_start=None, near=None):
        import pulp

        inst = self.inst
        prob = pulp.LpProblem("knapsack", pulp.LpMinimize)
        x = {}
        for i in range(inst.n):
            name = f"x{i}"
            if name in fixed:
                v = int(round(fixed[name]))
                x[name] = pulp.LpVariable(name, lowBound=v, upBound=v, cat="Continuous")
            elif name in relaxed:
                x[name] = pulp.LpVariable(name, lowBound=0, upBound=1, cat="Continuous")
            else:
                x[name] = pulp.LpVariable(name, cat="Binary")
                if warm_start and name in warm_start:
                    x[name].setInitialValue(int(round(warm_start[name])))
        prob += -pulp.lpSum(inst.values[i] * x[f"x{i}"] for i in range(inst.n))
        prob += pulp.lpSum(inst.weights[i] * x[f"x{i}"] for i in range(inst.n)) <= inst.capacity
        if near is not None:
            x_bar, k = near
            prob += pulp.lpSum((1 - v) if round(x_bar.get(n, 0.0)) >= 1 else v for n, v in x.items() if n not in fixed) <= k
        prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=max(1, int(round(time_limit))), warmStart=bool(warm_start)))
        self.last_objective = None
        if pulp.LpStatus[prob.status] not in ("Optimal", "Not Solved"):
            return None
        vals = {n: v.value() for n, v in x.items()}
        if any(val is None for val in vals.values()):
            return None
        self.last_objective = float(pulp.value(prob.objective))
        return {k: (float(v) if k in relaxed else float(round(v))) for k, v in vals.items()}


class KnapsackObjective:
    """Evaluador (`core.contracts.Evaluator`) + objetivo "de verdad" del `ProblemModel`.

    Se separa de `KnapsackModel.objective` (que el Protocol declara
    con firma `objective(sol) -> float`) porque en este ejemplo
    conviene penalizar la infactibilidad en vez de rechazarla, y para
    eso el evaluador necesita conocer `inst`. `bind(inst)` cierra
    sobre la instancia y devuelve un objeto que sí cumple
    `ProblemModel.objective(sol) -> float` y `Evaluator.full/incremental`.
    """

    def __init__(self, model: KnapsackModel, inst: KnapsackInstance, penalty: float = 1000.0):
        self.model = model
        self.inst = inst
        self.penalty = penalty

    def objective(self, sol: Solution) -> float:
        w = self.model.total_weight(self.inst, sol)
        value = sum(v for v, taken in zip(self.inst.values, sol) if taken)
        excess = max(0.0, w - self.inst.capacity)
        return -value + self.penalty * excess

    def is_feasible(self, sol: Solution) -> bool:
        return self.model.is_feasible(sol, self.inst)

    # --- Evaluator ---
    def full(self, sol: Solution) -> float:
        return self.objective(sol)

    def incremental(self, sol: Solution, m) -> float:
        i, new_val = m
        old = sol[i]
        if old == new_val:
            return self.objective(sol)
        toggled = sol[:i] + (new_val,) + sol[i + 1 :]
        return self.objective(toggled)


def bound_problem_model(inst: KnapsackInstance, penalty: float = 1000.0):
    """Combina `KnapsackModel` + `KnapsackObjective` en un único objeto que
    satisface completamente `core.contracts.ProblemModel` para `inst` fija.

    Esto es lo que se le pasa a `TrajectorySkeleton` y a los esqueletos
    de `skeletons/`.
    """
    base = KnapsackModel()
    obj = KnapsackObjective(base, inst, penalty=penalty)

    class _BoundModel:
        def load(self, path):
            return base.load(path)

        def is_feasible(self, sol):
            return obj.is_feasible(sol)

        def objective(self, sol):
            return obj.objective(sol)

        def build_mip(self, inst_):
            return base.build_mip(inst_)

        def to_assignment(self, sol):
            return base.to_assignment(sol)

        def from_assignment(self, x):
            return base.from_assignment(x)

        def variable_groups(self, inst_):
            return base.variable_groups(inst_)

    return _BoundModel()
