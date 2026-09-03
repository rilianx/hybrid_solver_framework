"""Descripción del CLSP para el generador LLM (§6) y micro-contextos de validación."""

from __future__ import annotations

import inspect
from random import Random

from core.validation import ValidationContext
from llm.prompts import ProblemSpec

from . import problem_model as pm
from .components import LotForLotConstructor, PeriodWindowDestruction


def make_spec() -> ProblemSpec:
    source = "\n\n".join(
        inspect.getsource(obj) for obj in (pm.CLSPInstance, pm.var_name, pm.LotSizingModel)
    )
    return ProblemSpec(
        name="Lot sizing capacitado multi-ítem (CLSP)",
        description=(
            "Hay `n_items` productos y `n_periods` períodos. Cada producto i tiene demanda d[i][t] por período, costo de setup "
            "s[i] (se paga en cada período en que se produce el ítem), costo de inventario h[i] por unidad almacenada al final "
            "de un período, y tiempo de setup st[i]. Cada período t tiene capacidad cap[t] compartida por todos los ítems: "
            "suma de producción x[i][t] más tiempos de setup de los ítems producidos <= cap[t]. No hay backlog: la demanda debe "
            "cubrirse con producción del período o inventario previo. Objetivo: minimizar setups + inventario. Un plan de setups "
            "que no alcanza a cubrir la demanda se penaliza fuertemente por unidad faltante (mucho más que cualquier setup; no se rechaza), así que la función "
            "objetivo siempre es finita."
        ),
        solution_representation=(
            "`sol` es una tupla de tuplas de bool: `sol[i][t]` es True si hay setup (se produce) del ítem i en el período t. "
            "Las cantidades x e inventarios se deciden óptimamente por un LP dado el patrón de setups, así que el componente "
            "solo decide DÓNDE hay setups. `problem.objective(sol)` resuelve ese LP (≈20-50 ms, cacheado por solución): úsalo "
            "con moderación dentro de `moves`/`delta`. `problem.inst` es la CLSPInstance (demand, setup_cost, holding_cost, "
            "setup_time, capacity, n_items, n_periods)."
        ),
        variable_naming=(
            "Las variables de la vista MIP son solo los setups: `y_{i}_{t}` (usa `var_name(i, t)` del módulo del problema). "
            "`problem.to_assignment(sol)` devuelve {var_name(i,t): 0.0/1.0}. `problem.variable_groups(inst)` agrupa por período: "
            "{'t0': [...], 't1': [...]}."
        ),
        problem_model_import="examples.lotsizing.problem_model",
        problem_model_source=source,
        notes=[
            "Estructura útil: mover un lote a un período anterior (producir antes y almacenar) ahorra un setup a cambio de inventario; "
            "un setup en un período sin demanda solo tiene sentido si cubre demanda futura; la capacidad acopla a los ítems dentro de cada período.",
            "Ideas de vecindarios distintos: apagar un setup y dejar que el LP redistribuya; mover un setup de t a t-1/t+1; "
            "intercambiar setups entre dos ítems en un período congestionado; fusionar dos setups consecutivos del mismo ítem.",
            "Ideas de destrucción distintas: por ventana de períodos, por ítem completo, por períodos con capacidad más saturada, "
            "por setups con menor 'utilidad' (lote pequeño).",
        ],
    )


def make_contexts(n_contexts: int = 2, n_items: int = 3, n_periods: int = 5, seed: int = 7) -> list[ValidationContext]:
    contexts = []
    for k in range(n_contexts):
        # Alternar instancias holgadas y ajustadas (utilización 0.95, tipo Trigeiro):
        # en las ajustadas la factibilidad y la capacidad compartida sí muerden.
        if k % 2 == 0:
            inst = pm.CLSPInstance.trigeiro(n_items, n_periods, Random(seed + k), utilization=0.95, tbo=2.0)
        else:
            inst = pm.CLSPInstance.random(n_items, n_periods, Random(seed + k))
        problem = pm.LotSizingModel(inst)
        contexts.append(
            ValidationContext(
                problem=problem,
                instances=[inst],
                trivial_solutions=[LotForLotConstructor().build(inst, Random(0))],
                baseline_constructor=LotForLotConstructor(),
                reference_destruction=PeriodWindowDestruction(inst),
                mip_time_limit=5.0,
                max_moves_checked=30,
            )
        )
    return contexts
