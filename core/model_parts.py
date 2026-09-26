"""El `ProblemModel` dividido en piezas verificables por separado.

Un `ProblemModel` de una pieza solo se puede validar entero: si la vista heurística y la
MIP no coinciden, el validador sabe que hay un error pero no dónde (corrida 19: "la
solución trivial es infactible en el MIP", sin decir qué restricción). Dividido, cada pieza
se verifica sola o contra las ya aceptadas y contra casos de prueba con respuesta conocida.

Piezas (funciones de un módulo; `inst` es la instancia):

  Vista heurística
    canonical(sol) -> sol                     forma canónica (idempotente)
    trivial_solution(inst) -> sol             una solución factible
    random_solution(inst, rng) -> sol         una solución al azar con estructura válida
    from_answer(inst, answer) -> sol          la respuesta en el formato neutral de los casos -> sol
    violations(inst, sol) -> {familia: magnitud}    > 0 = violada; {} o ceros si es factible
    cost_terms(inst, sol) -> {término: valor}       el objetivo, por términos (se minimiza la suma)

  Vista MIP, como datos (el framework arma el modelo del solver: `LinearMIP`)
    variables(inst) -> {nombre: (lo, hi, "binary" | "continuous")}
    structural_variables(inst) -> [nombres]   las que fija/libera una matheurística (binarias)
    to_assignment(inst, sol) -> {estructural: valor}
    aux_values(inst, sol) -> {auxiliar: valor}      valor de las demás variables en el punto `sol`
    from_assignment(inst, x) -> sol
    constraint_families(inst) -> {familia: [(coefs, sentido, lado_derecho), ...]}
        coefs = {variable: coeficiente}; sentido en "<=", ">=", "=="; el nombre de la familia
        (o su prefijo antes de un punto: "visita.entrada" -> "visita") es el de `violations`
    objective_terms(inst) -> {término: ({variable: coeficiente}, constante)}   mismos nombres que cost_terms
    variable_groups(inst) -> {grupo: [estructurales]}    partición, para Relax-and-Fix / Fix-and-Optimize

  Vista constructiva (opcional; la usa el constructor greedy modular `core.construction`, cuyo
  puntaje escribe el LLM en el slot `greedy_score`)
    empty_partial(inst) -> parcial            la solución parcial vacía
    candidates(inst, parcial) -> [acción]     acciones válidas: completar eligiendo cualquiera da una solución factible
    apply_action(inst, parcial, acción) -> parcial     parcial NUEVA (sin modificar la anterior)
    is_complete(inst, parcial) -> bool
    to_solution(inst, parcial) -> sol         en forma canónica
    complete_partial(inst, parcial, rng) -> sol        callejón sin salida (no quedan candidatos): terminar como se pueda

Por construcción desaparece una clase de errores: `objective` es la suma de `cost_terms` más
una penalización por las violaciones, e `is_feasible` es "no hay violaciones" (`PartsModel`).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

CONSTRUCTION_PARTS = ("empty_partial", "candidates", "apply_action", "is_complete", "to_solution", "complete_partial")
HEURISTIC_PARTS = ("canonical", "trivial_solution", "random_solution", "from_answer", "violations", "cost_terms")
MIP_PARTS = ("variables", "structural_variables", "to_assignment", "aux_values", "from_assignment",
             "constraint_families", "objective_terms", "variable_groups")
TOL = 1e-6
CACHE_SIZE = 50_000


def family_of(name: str) -> str:
    return name.split(".", 1)[0]


def lhs(coefs: dict[str, float], point: dict[str, float]) -> float:
    return sum(c * point.get(v, 0.0) for v, c in coefs.items())


def violated(constraint, point: dict[str, float], tol: float = TOL) -> float:
    """Cuánto viola la restricción `(coefs, sentido, rhs)` el punto (0 si se cumple)."""
    coefs, sense, rhs = constraint
    val = lhs(coefs, point)
    scale = tol * max(1.0, abs(rhs))
    if sense == "<=":
        return max(0.0, val - rhs - scale)
    if sense == ">=":
        return max(0.0, rhs - val - scale)
    if sense == "==":
        return max(0.0, abs(val - rhs) - scale)
    raise ValueError(f"sentido desconocido: {sense!r}")


@dataclass
class TestCase:
    """Un caso de prueba al estilo Codeforces: una micro-instancia y respuestas conocidas.

    `solutions`: [{"answer": <formato neutral>, "feasible": bool, "cost": float?, "violates": [familias]?}]
    `optimum`: costo óptimo de la instancia (None si no se da). `visible`: se muestra en el prompt.
    """

    name: str
    instance: Any
    solutions: list[dict]
    optimum: float | None = None
    visible: bool = False
    text: str = ""  # la instancia en el formato de entrada (para mostrar los casos visibles)


class LinearMIP:
    """`core.mip.MIPModel` genérico a partir de la vista MIP de las piezas (PuLP/CBC)."""

    def __init__(self, parts, inst):
        self.parts, self.inst = parts, inst
        self.last_objective: float | None = None
        self._vars = parts.variables(inst)
        self._struct = list(parts.structural_variables(inst))
        self._families = parts.constraint_families(inst)
        self._objective = parts.objective_terms(inst)

    def variables(self) -> list[str]:
        return list(self._struct)

    def solve(self, fixed, integer, relaxed, time_limit, warm_start=None, near=None):
        import pulp

        prob = pulp.LpProblem("parts", pulp.LpMinimize)
        x = {}
        struct = set(self._struct)
        for name, (lo, hi, kind) in self._vars.items():
            lo = None if lo is None or math.isinf(lo) else lo  # PuLP pide None para "sin cota"
            hi = None if hi is None or math.isinf(hi) else hi
            if name in fixed:
                v = float(fixed[name])
                x[name] = pulp.LpVariable(_safe(name), lowBound=v, upBound=v, cat="Continuous")
            elif name in struct and name in relaxed:
                x[name] = pulp.LpVariable(_safe(name), lowBound=lo, upBound=hi, cat="Continuous")
            else:
                cat = "Integer" if kind == "binary" else "Continuous"
                x[name] = pulp.LpVariable(_safe(name), lowBound=lo, upBound=hi, cat=cat)
                if warm_start and name in warm_start:
                    x[name].setInitialValue(warm_start[name])
        prob += pulp.lpSum(pulp.lpSum(c * x[v] for v, c in coefs.items()) + const
                           for coefs, const in self._objective.values())
        for fam, cons in self._families.items():
            for k, (coefs, sense, rhs) in enumerate(cons):
                expr = pulp.lpSum(c * x[v] for v, c in coefs.items())
                prob += (expr <= rhs) if sense == "<=" else (expr >= rhs) if sense == ">=" else (expr == rhs)
        if near is not None:
            x_bar, k = near
            prob += pulp.lpSum((1 - x[v]) if round(x_bar.get(v, 0.0)) >= 1 else x[v]
                               for v in self._struct if v not in fixed) <= k
        prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=max(0.1, float(time_limit)), warmStart=bool(warm_start)))
        self.last_objective = None
        if pulp.LpStatus[prob.status] not in ("Optimal", "Not Solved"):
            return None
        vals = {v: x[v].value() for v in self._struct}
        if any(val is None for val in vals.values()):
            return None
        self.last_objective = float(pulp.value(prob.objective))
        return {k: (float(v) if k in relaxed else float(round(v))) for k, v in vals.items()}


def _safe(name: str) -> str:
    return "v_" + "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)


class PartsConstructionView:
    """`core.contracts.ConstructionView` a partir de las piezas de la vista constructiva."""

    def __init__(self, parts, inst):
        self.parts, self.inst = parts, inst

    def empty(self):
        return self.parts.empty_partial(self.inst)

    def candidates(self, partial):
        return self.parts.candidates(self.inst, partial)

    def apply(self, partial, action):
        return self.parts.apply_action(self.inst, partial, action)

    def is_complete(self, partial) -> bool:
        return self.parts.is_complete(self.inst, partial)

    def to_solution(self, partial):
        return self.parts.to_solution(self.inst, partial)

    def complete(self, partial, rng):
        return self.parts.complete_partial(self.inst, partial, rng)


def has_construction(parts) -> bool:
    return all(callable(getattr(parts, n, None)) for n in CONSTRUCTION_PARTS)


class PartsModel:
    """`ProblemModel` ensamblado a partir de las piezas, ligado a una instancia."""

    def __init__(self, parts, inst, penalty: float | None = None):
        self.parts, self.inst = parts, inst
        if penalty is None:  # cualquier violación peor que la solución trivial entera
            triv = sum(parts.cost_terms(inst, parts.trivial_solution(inst)).values())
            penalty = 10.0 * (abs(triv) + 1.0)
        self.penalty = penalty
        self.validation_hints = getattr(parts, "VALIDATION_HINTS", {})
        # en el CLSP cada evaluación es un LP: las heurísticas reevalúan las mismas soluciones
        if has_construction(parts):  # solo si la hay: el validador de greedy_score mira si el modelo la expone
            self.construction_view = lambda inst: PartsConstructionView(self.parts, inst)
        self._viol: dict[Any, dict[str, float]] = {}
        self._cost: dict[Any, float] = {}

    def violations(self, sol) -> dict[str, float]:
        if sol not in self._viol:
            if len(self._viol) > CACHE_SIZE:
                self._viol.clear()
            self._viol[sol] = {k: v for k, v in self.parts.violations(self.inst, sol).items() if v > TOL}
        return self._viol[sol]

    def objective(self, sol) -> float:
        if sol not in self._cost:
            if len(self._cost) > CACHE_SIZE:
                self._cost.clear()
            self._cost[sol] = sum(self.parts.cost_terms(self.inst, sol).values())
        return self._cost[sol] + self.penalty * sum(self.violations(sol).values())

    def is_feasible(self, sol) -> bool:
        return not self.violations(sol)

    def explain_infeasibility(self, sol) -> str:
        v = self.violations(sol)
        return "; ".join(f"{k}: {m:g}" for k, m in v.items()) or "factible"

    def build_mip(self, inst) -> LinearMIP:
        return LinearMIP(self.parts, inst)

    def to_assignment(self, sol) -> dict[str, float]:
        return self.parts.to_assignment(self.inst, sol)

    def from_assignment(self, x: dict[str, float]):
        return self.parts.from_assignment(self.inst, x)

    def variable_groups(self, inst) -> dict[str, list[str]]:
        return self.parts.variable_groups(inst)

    def random_solution(self, rng):
        return self.parts.random_solution(self.inst, rng)


__all__ = ["CONSTRUCTION_PARTS", "HEURISTIC_PARTS", "MIP_PARTS", "PartsConstructionView", "has_construction", "LinearMIP", "PartsModel", "TestCase", "family_of", "lhs", "violated"]
