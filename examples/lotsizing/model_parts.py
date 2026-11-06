"""El oráculo del CLSP (`core.model_parts`, vista heurística): qué es una solución, qué viola y cuánto cuesta. Es la
referencia contra la que se valida lo que escribe el LLM (el modelo C++ y la vista MIP) y con la que se generan los
casos de prueba (`cases.py`).

Solución: la matriz de setups `y[i][t]` (tupla de tuplas de bool), la misma representación que
los componentes del CLSP. Dados los setups, el plan de producción sale de un LP: producir lo más
posible de la demanda (sin backlog: la demanda de t se cubre con producción de t o anterior) y,
entre esos planes, el de menor inventario. De ese plan salen las familias y los términos:

  Familias: `demanda` (unidades que esos setups no alcanzan a cubrir; la capacidad nunca se viola
  porque el LP la respeta). Términos: `setup` (costo de los setups encendidos) e `inventario`
  (costo de mantener el inventario de fin de período).

La vista MIP la escribe el LLM (`llm.native_mip_generator`, `generated/clsp_native/mip/mip.py`).
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


def well_formed(inst: CLSPInstance, sol) -> str | None:
    """La forma de la solución: una fila por ítem con un valor por período."""
    if len(sol) != inst.n_items:
        return f"se esperaba una fila por ítem ({inst.n_items}) y hay {len(sol)}"
    lens = {len(r) for r in sol}
    return None if lens == {inst.n_periods} else f"filas de largo {sorted(lens)} y hay {inst.n_periods} períodos"
