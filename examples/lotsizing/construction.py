"""Vista constructiva del CLSP (`core.contracts.ConstructionView`).

Estado parcial: cuánto de cada demanda d[i][t] falta cubrir (`rem`), cuánta capacidad
de cada período ya se usó (`used`, producción + tiempos de setup) y qué setups están
encendidos (`setup`). Acción: cubrir demanda pendiente del ítem i con deadline t
produciendo en un período s ≤ t (sin backlog) la cantidad q = mín(pendiente, capacidad
libre de s). Los deadlines se recorren en orden (el período t* más temprano con demanda
pendiente); el puntaje decide qué ítem de t* se cubre y desde qué período.

Factibilidad. Con tiempos de setup, decidir si un plan parcial se puede completar es
NP-completo, así que el filtro de candidatos usa una condición NECESARIA y barata: para
cada T ≥ t*, la capacidad libre en los períodos ≤ T alcanza para la demanda pendiente
con deadline ≤ T más un setup por cada ítem que todavía no tiene setup encendido en
ningún período ≤ su primer deadline pendiente. Si igual se llega a un callejón sin
salida (la capacidad libre quedó fragmentada en pedazos menores que un tiempo de
setup), `complete` fija los setups ya decididos y resuelve el resto con el MIP.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

from .problem_model import CLSPInstance, var_name

EPS = 1e-7


@dataclass(frozen=True)
class CoverAction:
    """Cubrir `qty` unidades de la demanda (item, period) produciendo en `source` ≤ period.
    `new_setup` es True si hay que encender el setup de `item` en `source`."""

    item: int
    period: int
    source: int
    qty: float
    new_setup: bool


class CLSPPartial:
    """Estado parcial (se copia en cada `apply`; nunca se modifica en su lugar).

    Atributos que puede leer un puntaje:
      inst                  la CLSPInstance (demand, setup_cost, holding_cost, setup_time, capacity)
      rem[i][t]             demanda pendiente del ítem i con deadline t
      used[t]               capacidad ya usada en t (producción + tiempos de setup)
      setup[i][t]           True si el setup del ítem i en t ya está encendido
      free(t)               capacidad libre en t
      pending_total()       demanda pendiente total
    """

    __slots__ = ("inst", "rem", "used", "setup")

    def __init__(self, inst: CLSPInstance, rem, used, setup):
        self.inst, self.rem, self.used, self.setup = inst, rem, used, setup

    def free(self, t: int) -> float:
        return self.inst.capacity[t] - self.used[t]

    def pending_total(self) -> float:
        return sum(sum(row) for row in self.rem)

    def copy(self) -> "CLSPPartial":
        return CLSPPartial(self.inst, [list(r) for r in self.rem], list(self.used), [list(r) for r in self.setup])


class CLSPConstructionView:
    def __init__(self, problem, inst: CLSPInstance, mip_time_limit: float = 2.0):
        self.problem, self.inst, self.mip_time_limit = problem, inst, mip_time_limit

    def empty(self) -> CLSPPartial:
        inst = self.inst
        return CLSPPartial(inst, [list(r) for r in inst.demand], [0.0] * inst.n_periods,
                           [[False] * inst.n_periods for _ in range(inst.n_items)])

    def _next_deadline(self, p: CLSPPartial) -> int | None:
        for t in range(self.inst.n_periods):
            if any(p.rem[i][t] > EPS for i in range(self.inst.n_items)):
                return t
        return None

    def _slack(self, p: CLSPPartial, t0: int) -> tuple[list[float], list[list[bool]]]:
        """slack[T] para T ≥ t0 (capacidad libre acumulada − demanda pendiente acumulada −
        reserva de setups) y needs[i][T]: si el ítem i cuenta en la reserva de T."""
        inst, n, T_ = self.inst, self.inst.n_items, self.inst.n_periods
        first_pending = [next((t for t in range(T_) if p.rem[i][t] > EPS), None) for i in range(n)]
        has_setup_by = [[False] * T_ for _ in range(n)]
        for i in range(n):
            acc = False
            for t in range(T_):
                acc = acc or p.setup[i][t]
                has_setup_by[i][t] = acc
        slack, needs = [0.0] * T_, [[False] * T_ for _ in range(n)]
        cap_acc = dem_acc = 0.0
        for T in range(T_):
            cap_acc += p.free(T)
            dem_acc += sum(p.rem[i][T] for i in range(n))
            if T < t0:
                continue
            reserve = 0.0
            for i in range(n):
                f = first_pending[i]
                if f is not None and f <= T and not has_setup_by[i][f]:
                    needs[i][T] = True
                    reserve += inst.setup_time[i]
            slack[T] = cap_acc - dem_acc - reserve
        return slack, needs

    def candidates(self, p: CLSPPartial):
        t = self._next_deadline(p)
        if t is None:
            return []
        inst = self.inst
        slack, needs = self._slack(p, t)
        out = []
        for i in range(inst.n_items):
            if p.rem[i][t] <= EPS:
                continue
            for s in range(t, -1, -1):
                new = not p.setup[i][s]
                avail = p.free(s) - (inst.setup_time[i] if new else 0.0)
                if avail <= EPS:
                    continue
                q = min(p.rem[i][t], avail)
                # Efecto en slack[T], T ≥ t: el setup nuevo consume st[i] de capacidad, salvo
                # que el ítem ya estuviera en la reserva de T (entonces solo se "cobra" la reserva).
                if new and any(slack[T] - inst.setup_time[i] < -EPS for T in range(t, inst.n_periods) if not needs[i][T]):
                    continue
                out.append(CoverAction(i, t, s, q, new))
        return out

    def apply(self, p: CLSPPartial, a: CoverAction) -> CLSPPartial:
        n = p.copy()
        n.rem[a.item][a.period] = max(0.0, n.rem[a.item][a.period] - a.qty)
        n.used[a.source] += a.qty + (self.inst.setup_time[a.item] if a.new_setup else 0.0)
        n.setup[a.item][a.source] = True
        return n

    def is_complete(self, p: CLSPPartial) -> bool:
        return self._next_deadline(p) is None

    def to_solution(self, p: CLSPPartial):
        return tuple(tuple(row) for row in p.setup)

    def complete(self, p: CLSPPartial, rng: Random):
        """Callejón sin salida: fija en 1 los setups ya encendidos y deja que el MIP decida
        el resto (con tiempo límite). Si el MIP no encuentra nada, devuelve los setups
        decididos más lot-for-lot para lo pendiente (puede quedar infactible)."""
        inst = self.inst
        fixed = {var_name(i, t): 1.0 for i in range(inst.n_items) for t in range(inst.n_periods) if p.setup[i][t]}
        model = self.problem.build_mip(inst)
        free = [v for v in model.variables() if v not in fixed]
        x = model.solve(fixed=fixed, integer=set(free), relaxed=set(), time_limit=self.mip_time_limit)
        if x is not None:
            return self.problem.from_assignment(x)
        return tuple(tuple(p.setup[i][t] or p.rem[i][t] > EPS for t in range(inst.n_periods)) for i in range(inst.n_items))


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
