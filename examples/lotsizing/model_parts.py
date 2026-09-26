"""El modelo del CLSP escrito como piezas (`core.model_parts`): la referencia contra la que se
prueba el mecanismo y con la que se generan los casos de prueba (`cases.py`).

Solución: la matriz de setups `y[i][t]` (tupla de tuplas de bool), la misma representación que
los componentes del CLSP. Dados los setups, el plan de producción sale de un LP: producir lo más
posible de la demanda (sin backlog: la demanda de t se cubre con producción de t o anterior) y,
entre esos planes, el de menor inventario. De ese plan salen las familias y los términos:

  Familias: `demanda` (unidades que esos setups no alcanzan a cubrir; la capacidad nunca se viola
  porque el LP la respeta). Términos: `setup` (costo de los setups encendidos) e `inventario`
  (costo de mantener el inventario de fin de período).

MIP: `y_i_t` binarias (estructurales), producción `x_i_t` e inventario `s_i_t` continuas
(auxiliares, su valor en el punto de una solución es el del plan del LP). Familias
`demanda.balance` (s_{t-1} + x_t − s_t = d_t), `capacidad` (Σ x + st·y <= cap) y `enlace`
(x <= M·y). Grupos: uno por período (Relax-and-Fix y Fix-and-Optimize recorren el horizonte).
"""

from __future__ import annotations

from functools import lru_cache
from random import Random

import pulp

from .instance import CLSPInstance


def canonical(sol):
    return tuple(tuple(bool(v) for v in row) for row in sol)


def trivial_solution(inst: CLSPInstance):
    """Todos los setups encendidos. Factible en las instancias del generador: su capacidad cubre la
    demanda acumulada más un tiempo de setup por ítem y período en cada prefijo del horizonte."""
    return tuple(tuple(True for _ in range(inst.n_periods)) for _ in range(inst.n_items))


def random_solution(inst: CLSPInstance, rng: Random):
    p = rng.uniform(0.2, 0.8)
    return tuple(tuple(rng.random() < p for _ in range(inst.n_periods)) for _ in range(inst.n_items))


def from_answer(inst: CLSPInstance, answer):
    return canonical(answer)


@lru_cache(maxsize=4096)
def _plan(inst: CLSPInstance, sol) -> tuple[dict, dict, float]:
    """(x, s, faltante) del plan con los setups fijos: primero cubrir, después menos inventario."""
    I, T = range(inst.n_items), range(inst.n_periods)
    big = 1.0 + sum(inst.holding_cost) * inst.n_periods * 10.0  # cubrir una unidad vale más que todo el inventario
    prob = pulp.LpProblem("plan", pulp.LpMinimize)
    x = {(i, t): pulp.LpVariable(f"x_{i}_{t}", lowBound=0) for i in I for t in T}
    s = {(i, t): pulp.LpVariable(f"s_{i}_{t}", lowBound=0) for i in I for t in T}
    u = {(i, t): pulp.LpVariable(f"u_{i}_{t}", lowBound=0) for i in I for t in T}
    for i in I:
        for t in T:
            prev = s[i, t - 1] if t > 0 else 0
            prob += prev + x[i, t] + u[i, t] - s[i, t] == inst.demand[i][t]
            if not sol[i][t]:
                prob += x[i, t] == 0
    for t in T:
        prob += pulp.lpSum(x[i, t] + inst.setup_time[i] * sol[i][t] for i in I) <= inst.capacity[t]
    prob += pulp.lpSum(big * u[k] + inst.holding_cost[k[0]] * s[k] for k in u)
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    val = lambda v: max(0.0, v.value() or 0.0)  # noqa: E731
    return ({k: val(v) for k, v in x.items()}, {k: val(v) for k, v in s.items()}, sum(val(v) for v in u.values()))


def violations(inst: CLSPInstance, sol) -> dict[str, float]:
    return {"demanda": _plan(inst, canonical(sol))[2]}


def cost_terms(inst: CLSPInstance, sol) -> dict[str, float]:
    _, s, _ = _plan(inst, canonical(sol))
    setup = sum(inst.setup_cost[i] for i in range(inst.n_items) for t in range(inst.n_periods) if sol[i][t])
    return {"setup": float(setup), "inventario": sum(inst.holding_cost[i] * v for (i, _t), v in s.items())}


# ---------------------------------------------------------------- vista MIP
def _y(i, t):
    return f"y_{i}_{t}"


def structural_variables(inst: CLSPInstance):
    return [_y(i, t) for i in range(inst.n_items) for t in range(inst.n_periods)]


def variables(inst: CLSPInstance):
    out = {v: (0.0, 1.0, "binary") for v in structural_variables(inst)}
    for i in range(inst.n_items):
        total = float(sum(inst.demand[i]))
        for t in range(inst.n_periods):
            out[f"x_{i}_{t}"] = (0.0, total, "continuous")
            out[f"s_{i}_{t}"] = (0.0, total, "continuous")
    return out


def to_assignment(inst: CLSPInstance, sol):
    return {_y(i, t): float(sol[i][t]) for i in range(inst.n_items) for t in range(inst.n_periods)}


def aux_values(inst: CLSPInstance, sol):
    x, s, _ = _plan(inst, canonical(sol))
    return {**{f"x_{i}_{t}": v for (i, t), v in x.items()}, **{f"s_{i}_{t}": v for (i, t), v in s.items()}}


def from_assignment(inst: CLSPInstance, x):
    return tuple(tuple((x.get(_y(i, t)) or 0.0) >= 0.5 for t in range(inst.n_periods)) for i in range(inst.n_items))


def constraint_families(inst: CLSPInstance):
    I, T = range(inst.n_items), range(inst.n_periods)
    balance = []
    for i in I:
        for t in T:
            coefs = {f"x_{i}_{t}": 1.0, f"s_{i}_{t}": -1.0}
            if t > 0:
                coefs[f"s_{i}_{t - 1}"] = 1.0
            balance.append((coefs, "==", float(inst.demand[i][t])))
    capacity = [({**{f"x_{i}_{t}": 1.0 for i in I}, **{_y(i, t): float(inst.setup_time[i]) for i in I}}, "<=", float(inst.capacity[t]))
                for t in T]
    link = [({f"x_{i}_{t}": 1.0, _y(i, t): -float(sum(inst.demand[i]))}, "<=", 0.0) for i in I for t in T]
    return {"demanda.balance": balance, "capacidad": capacity, "enlace": link}


def objective_terms(inst: CLSPInstance):
    I, T = range(inst.n_items), range(inst.n_periods)
    return {"setup": ({_y(i, t): float(inst.setup_cost[i]) for i in I for t in T}, 0.0),
            "inventario": ({f"s_{i}_{t}": float(inst.holding_cost[i]) for i in I for t in T}, 0.0)}


def variable_groups(inst: CLSPInstance):
    return {f"t{t}": [_y(i, t) for i in range(inst.n_items)] for t in range(inst.n_periods)}


# ---------------------------------------------------------------- vista constructiva
# La de `construction.py` (cubrir la demanda del deadline más temprano desde un período anterior
# con capacidad). En un callejón sin salida se encienden todos los setups (el plan trivial, factible).
def _view(inst: CLSPInstance):
    from .construction import CLSPConstructionView

    return CLSPConstructionView(None, inst)


def empty_partial(inst: CLSPInstance):
    return _view(inst).empty()


def candidates(inst: CLSPInstance, partial):
    return _view(inst).candidates(partial)


def apply_action(inst: CLSPInstance, partial, action):
    return _view(inst).apply(partial, action)


def is_complete(inst: CLSPInstance, partial) -> bool:
    return _view(inst).is_complete(partial)


def to_solution(inst: CLSPInstance, partial):
    return canonical(partial.setup)


def complete_partial(inst: CLSPInstance, partial, rng):
    return trivial_solution(inst)
