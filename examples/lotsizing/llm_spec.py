"""Descripción del CLSP para el generador LLM (§6) y micro-contextos de validación."""

from __future__ import annotations

import inspect
from random import Random

from core.validation import ValidationContext
from core.validation.base import DiversityProbe
from llm.prompts import ProblemSpec

from . import problem_model as pm
from .components import LotForLotConstructor, PeriodWindowDestruction, SetupFlipNeighborhood


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
        starting_solution=starting_solution_example(),
        construction_source=_construction_source(),
        slot_hints={
            "constructor": (
                "Factible significa cubrir TODA la demanda respetando la capacidad de cada período. Con utilización alta "
                "esto NO es trivial: lot-for-lot (setup justo donde hay demanda) puede exceder la capacidad de un período pico "
                "y dejar faltante, y entonces hay que producir ANTES y almacenar. Regla práctica: recorre los períodos en "
                "orden; si la demanda acumulada hasta t (más tiempos de setup) supera la capacidad acumulada disponible, "
                "adelanta producción a períodos anteriores con holgura."
            ),
            "greedy_score": "En el CLSP: qué cubrir primero y desde dónde (costo, urgencia, holgura de capacidad, balance entre ítems).",
        },
    )


def _construction_source() -> str:
    """Lo que ve el LLM al escribir un `greedy_score`: la acción, el estado parcial y cómo se
    generan los candidatos (sin los puntajes escritos a mano)."""
    from . import construction as c

    return "\n\n".join(inspect.getsource(o) for o in (c.CoverAction, c.CLSPPartial)) + (
        "\n\n# Candidatos en cada paso: t* = el período más temprano con demanda pendiente; para cada ítem i con\n"
        "# rem[i][t*] > 0 y cada período s <= t* con capacidad libre (descontando el tiempo de setup si hay que\n"
        "# encenderlo), una CoverAction(i, t*, s, q, new_setup) con q = min(pendiente, capacidad libre). Ya vienen\n"
        "# filtrados por capacidad acumulada. `score` elige cuál conviene; menor = mejor."
    )


def _feasible_trivial(problem, inst):
    """Solución trivial GARANTIZADA factible: lot-for-lot si lo es; si no, Relax-and-Fix.

    Lot-for-lot produce justo en el período de la demanda, y con la capacidad
    ajustada el tiempo de setup de todos los ítems puede exceder el pico: en
    ese caso deja faltante y NO sirve como referencia de factibilidad.
    """
    from core.fixing_policies import SlidingWindowPolicy
    from skeletons.relax_and_fix import RelaxAndFixConstructor

    lfl = LotForLotConstructor()
    sol = lfl.build(inst, Random(0))
    if problem.is_feasible(sol):
        return sol
    rf = RelaxAndFixConstructor(problem, SlidingWindowPolicy(2, 1), time_limit_per_window=5, fallback=lfl)
    sol = rf.build(inst, Random(0))
    return sol if problem.is_feasible(sol) else None


def make_diversity_probe(n_items: int = 10, n_periods: int = 15, seed: int = 100) -> DiversityProbe | None:
    """Sonda de diversidad: instancia de tamaño realista (la misma familia que usa el
    benchmark) donde se mide si dos componentes son el mismo operador con otro nombre.

    Por qué no la micro-instancia (corrida 6): en 3×5 hay 15 variables y casi cualquier
    par de vecindarios se solapa poco por falta de espacio — `congestion_rollback` daba
    Jaccard 0,60 contra `setup_flip` (pasaba el gate de 0,80) y 0,93 en 10×15, donde el
    benchmark lo mostró como duplicado (+1,2% vs +29,8%).
    """
    inst = pm.CLSPInstance.trigeiro(n_items, n_periods, Random(seed), utilization=0.95, tbo=3.0)
    problem = pm.LotSizingModel(inst)
    sol = _feasible_trivial(problem, inst)
    if sol is None:
        return None
    return DiversityProbe(problem=problem, solution=sol, max_similarity=0.8)


def make_combination_probe(probe: DiversityProbe | None, budget: float = 1.0):
    """Sonda de combinación sobre la instancia 10×15 de la sonda de diversidad: socios de mano
    para los demás slots y dos partidas (lot-for-lot y el greedy de costo marginal). Es
    infraestructura de validación: el LLM no la ve, así que vale también desde cero."""
    from core.assembler import Assembler
    from core.component import ComponentSpec
    from core.validation.combination import CombinationProbe

    if probe is None:
        return None

    def assembler_for(slot, components):
        from .catalog import build_registry

        # Sin los componentes de mano de ESTE slot: en VNS harían el trabajo del shake.
        registry = build_registry(exclude_slots={slot})
        names = []
        for component, factory in components:
            spec = dict(component)
            spec.pop("combination_gains", None)
            registry.register(ComponentSpec.from_dict(spec, factory))
            names.append(spec["name"])
        assembler = Assembler(problem_factory=pm.LotSizingModel, registry=registry)
        assembler.probe_component = names[0]
        return assembler

    return CombinationProbe(instance=probe.problem.inst, assembler_for=assembler_for,
                            starts=["lot_for_lot", "greedy_unit_marginal_cost"], budget=budget)


def make_contexts(
    n_contexts: int = 2, n_items: int = 3, n_periods: int = 5, seed: int = 7, strict: bool = True,
    reference_free: bool = False, combination: bool = False,
) -> list[ValidationContext]:
    """Micro-contextos de validación.

    `strict=True` (generación con LLM): exige que un vecindario mejore desde la
    solución de PARTIDA, no solo desde soluciones aleatorias — empuja al modelo a
    operadores útiles donde el esqueleto arranca. `strict=False` (admisión al
    catálogo): tolera operadores estrechos, que pueden valer en combinación.

    `reference_free=True` (generación desde cero): sin vecindario de referencia, así el
    feedback de "no mejora desde la partida" no le muestra al modelo los movimientos de
    `setup_flip`. La solución trivial (lot-for-lot o Relax-and-Fix) se mantiene: es la
    partida del esqueleto y la base de las pruebas, no una pista de diseño.
    """
    # Una sola sonda compartida por todos los contextos (construirla cuesta un MIP chico).
    # También en modo leniente: la admisión al catálogo relaja solo `improves_from_start`,
    # no la factibilidad en tamaño realista. Sin sonda entraba un constructor que la
    # generación había abandonado por infactible (`batch_covering_merge`, corrida 9) y el
    # tuner perdía 12 de 40 trials en él.
    probe = make_diversity_probe()
    combo = make_combination_probe(probe) if combination else None
    contexts = []
    k, retry = 0, 0
    while len(contexts) < n_contexts and retry < 10:
        # Semilla estable por posición k (retry solo cambia si la instancia se descarta),
        # así los tests y las corridas son reproducibles. Alternar ajustadas / holgadas.
        rng = Random(seed + k + 1000 * retry)
        if k % 2 == 0:
            inst = pm.CLSPInstance.trigeiro(n_items, n_periods, rng, utilization=0.95, tbo=2.0)
        else:
            inst = pm.CLSPInstance.random(n_items, n_periods, rng)
        problem = pm.LotSizingModel(inst)
        trivial = _feasible_trivial(problem, inst)
        if trivial is None:
            retry += 1
            continue  # instancia sin solución trivial factible: se reintenta con otra semilla
        k, retry = k + 1, 0
        contexts.append(
            ValidationContext(
                problem=problem,
                instances=[inst],
                trivial_solutions=[trivial],
                baseline_constructor=LotForLotConstructor(),
                reference_destruction=PeriodWindowDestruction(inst),
                reference_neighborhood=None if reference_free else SetupFlipNeighborhood(problem),  # verdad-terreno para el feedback
                mip_time_limit=5.0,
                max_moves_checked=30,
                require_improving_from_start=strict,
                diversity_probe=probe,
                combination=combo,
            )
        )
    return contexts


def starting_solution_example(n_items: int = 3, n_periods: int = 6, seed: int = 11) -> str:
    """Texto para el prompt: una micro-instancia y su solución lot-for-lot, para que el
    LLM vea DESDE DÓNDE arranca el esqueleto y diseñe movimientos que mejoren desde ahí."""
    inst = pm.CLSPInstance.trigeiro(n_items, n_periods, Random(seed), utilization=0.95, tbo=2.0)
    sol = LotForLotConstructor().build(inst, Random(0))
    lines = ["demanda d[i][t] (filas = ítems, columnas = períodos t0..t%d):" % (n_periods - 1)]
    for i in range(n_items):
        lines.append("  i%d: " % i + " ".join(f"{int(d):>4}" for d in inst.demand[i]))
    lines.append(f"setup_cost = {[int(c) for c in inst.setup_cost]}, holding_cost = {[int(h) for h in inst.holding_cost]}, "
                 f"setup_time = {list(inst.setup_time)}, capacity = {int(inst.capacity[0])} por período")
    lines.append("solución de PARTIDA (lot-for-lot: setup exactamente donde hay demanda), sol[i][t]:")
    for i in range(n_items):
        lines.append("  i%d: " % i + " ".join("  ■ " if v else "  · " for v in sol[i]))
    lines.append("Desde aquí, un movimiento MEJORA si ahorra un setup a cambio de inventario: p.ej. apagar el setup de un ítem "
                 "en t y dejar que la producción de t-1 (donde ya hay setup) cubra ambos períodos, si la capacidad de t-1 alcanza. "
                 "Un movimiento que solo desplaza un setup a un período sin demanda AGREGA inventario y no mejora; "
                 "uno que apaga un setup sin setup anterior deja demanda sin cubrir (penalización enorme).")
    return "\n".join(lines)
