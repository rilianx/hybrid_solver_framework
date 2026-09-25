"""Descripción del CVRP para el generador LLM (§6) y micro-contextos de validación."""

from __future__ import annotations

import inspect
from random import Random

from core.validation import ValidationContext
from core.validation.base import DiversityProbe
from llm.prompts import ProblemSpec

from . import problem_model as pm
from .components import RandomRemoval, RelocateNeighborhood, SingletonRoutes


def make_spec() -> ProblemSpec:
    source = "\n\n".join(inspect.getsource(obj) for obj in (
        pm.canonical, pm.var_name, pm.CVRPInstance, pm.route_length, pm.route_load, pm.CVRPModel))
    return ProblemSpec(
        name="Ruteo de vehículos con capacidad (CVRP), flota libre",
        description=(
            "Hay un depósito (nodo 0) y `n_customers` clientes (nodos 1..n) con coordenadas en el plano y demanda d[c]. "
            "Cada vehículo sale del depósito, visita una secuencia de clientes y vuelve; la suma de demandas de una ruta no "
            "puede superar la capacidad Q. Cada cliente se visita exactamente una vez. La cantidad de vehículos es libre. "
            "Objetivo: minimizar la distancia euclidiana total. Una solución que excede la capacidad o deja clientes sin "
            "visitar (o los repite) se penaliza fuertemente (no se rechaza), así que el objetivo siempre es finito."
        ),
        solution_representation=(
            "`sol` es una tupla de rutas; cada ruta es una tupla de clientes (enteros 1..n) en el orden de visita, sin el "
            "depósito. Forma CANÓNICA obligatoria: sin rutas vacías y ordenadas por su primer cliente; construye siempre la "
            "solución que devuelves con `canonical(rutas)` (importable del módulo del problema). Como la forma canónica "
            "reordena las rutas, describe los movimientos por CLIENTES y no por índices de ruta, e incluye en el movimiento lo "
            "necesario para deshacerlo (p.ej. el predecesor y sucesor originales, con 0 = depósito). `problem.objective(sol)` "
            "cuesta O(n); `problem.inst.dist(i, j)` es barato, así que `delta` puede calcularse con unas pocas distancias. "
            "`problem.inst` es la CVRPInstance (coords, demand, capacity, n_customers, customers, dist)."
        ),
        variable_naming=(
            "Las variables de la vista MIP son los arcos dirigidos `x_{i}_{j}` (i ≠ j, 0 = depósito; usa `var_name(i, j)`). "
            "`problem.to_assignment(sol)` devuelve {var_name(i,j): 0.0/1.0} para TODOS los arcos. `problem.variable_groups(inst)` "
            "agrupa los arcos por sector angular del cliente de salida: {'s0': [...], 's1': [...]}."
        ),
        problem_model_import="examples.cvrp.problem_model",
        problem_model_source=source,
        notes=[
            "Estructura útil: los clientes cercanos entre sí conviene atenderlos en la misma ruta; una ruta con holgura de "
            "carga puede absorber clientes de otra; dos rutas que se cruzan en el plano casi siempre se pueden mejorar.",
            "Ideas de vecindarios distintos: mover un cliente (relocate), intercambiar dos clientes (swap), mover un tramo "
            "de 2–3 clientes (or-opt), invertir un tramo de una ruta (2-opt), cruzar las colas de dos rutas (2-opt*).",
            "Ideas de destrucción distintas: clientes al azar, clientes cercanos a uno (radial), una o dos rutas completas, "
            "los clientes con mayor costo de desvío. Para el sub-MIP, libera los arcos entre los clientes quitados, sus "
            "vecinos de ruta y el depósito, para que pueda reinsertarlos y cerrar los huecos.",
        ],
        starting_solution=starting_solution_example(),
        construction_source=_construction_source(),
        slot_hints={
            "constructor": ("Factible significa: cada cliente exactamente una vez y cada ruta con carga <= capacidad. Con "
                            "flota libre siempre puedes abrir otra ruta, así que la factibilidad es fácil; la calidad está en "
                            "agrupar clientes cercanos."),
            "greedy_score": "En el CVRP: a qué cliente atender primero y dónde insertarlo (desvío, cercanía, holgura de carga).",
        },
    )


def make_model_spec():
    """Para generar el `ProblemModel` completo con LLM (§6.1): la descripción y la instancia, sin
    el modelo de referencia."""
    from llm.model_generator import ModelSpec

    from . import instance

    return ModelSpec(
        name="CVRP (ruteo de vehículos con capacidad, flota libre)",
        description=(
            "Hay un depósito (nodo 0) y clientes 1..n con coordenadas y demanda d[c] (`inst.demand[0] = 0`). Cada vehículo "
            "sale del depósito, visita una secuencia de clientes y vuelve al depósito; la suma de demandas de una ruta no "
            "puede superar `inst.capacity`. Cada cliente se visita exactamente una vez. La cantidad de vehículos es libre "
            "(no hay límite ni costo fijo por vehículo). Objetivo: minimizar la distancia euclidiana total recorrida "
            "(`inst.dist(i, j)`), incluidos los tramos desde y hacia el depósito. Una solución infactible debe tener un "
            "objetivo finito pero peor que cualquier factible (penalización)."
        ),
        instance_source=inspect.getsource(instance.CVRPInstance),
        instance_import="examples.cvrp.instance",
        notes=["Elige tú la representación de la solución para las heurísticas (debe ser hashable y comparable con ==)."],
        forbidden_modules=["examples.cvrp.problem_model", "examples.cvrp.components", "examples.cvrp.construction",
                           "examples.cvrp.model_parts", "examples.cvrp.cases"],
        answer_format=("Lista de rutas; cada ruta, una lista de clientes (enteros 1..n) en orden de visita, sin el depósito. "
                       "Ejemplo: [[3, 1], [2, 4]]. Dos respuestas con las mismas rutas en otro orden de rutas son la misma solución."),
        families=("Familias de restricciones: `visita` (cada cliente exactamente una vez; magnitud = cuántas visitas sobran o "
                  "faltan) y `capacidad` (magnitud = exceso de carga total). Término del objetivo: `distancia`."),
    )


def _construction_source() -> str:
    from . import construction as c

    return "\n\n".join(inspect.getsource(o) for o in (c.InsertAction, c.CVRPPartial)) + (
        "\n\n# Candidatos en cada paso: para cada cliente pendiente c, cada posición de cada ruta abierta donde cabe su\n"
        "# demanda (InsertAction(c, k, pos, delta, False), con delta = aumento de distancia) y además abrir una ruta nueva\n"
        "# (InsertAction(c, len(routes), 0, 2*dist(0, c), True)). `score` elige cuál conviene; menor = mejor."
    )


def greedy_start(problem):
    """Partida de validación con estructura (inserción más barata). Una ruta por cliente es
    degenerada como partida: desde ahí solo mejora juntar clientes, y operadores legítimos
    (intercambio, or-opt, 2-opt) no tienen ninguna mejora (corrida 20)."""
    from core.construction import GreedyConstructor

    from .construction import CheapestInsertion

    return GreedyConstructor(problem, CheapestInsertion(problem))


def make_diversity_probe(n_customers: int = 30, seed: int = 100) -> DiversityProbe:
    """Sonda de tamaño realista, desde la partida greedy (ver `greedy_start`)."""
    inst = pm.CVRPInstance.random(n_customers, Random(seed))
    problem = pm.CVRPModel(inst)
    return DiversityProbe(problem=problem, solution=greedy_start(problem).build(inst, Random(0)), max_similarity=0.8)


def make_combination_probe(probe: DiversityProbe | None, budget: float = 1.0):
    """Corridas cortas del componente en cada esqueleto que declara, desde la partida trivial y
    desde el greedy de inserción más barata (ver `core.validation.combination`)."""
    from core.assembler import Assembler
    from core.component import ComponentSpec
    from core.validation.combination import CombinationProbe

    if probe is None:
        return None

    def assembler_for(slot, components):
        from .catalog import build_registry

        registry = build_registry(exclude_slots={slot})
        names = []
        for component, factory in components:
            spec = dict(component)
            spec.pop("combination_gains", None)
            registry.register(ComponentSpec.from_dict(spec, factory))
            names.append(spec["name"])
        assembler = Assembler(problem_factory=pm.CVRPModel, registry=registry)
        assembler.probe_component = names[0]
        return assembler

    return CombinationProbe(instance=probe.problem.inst, assembler_for=assembler_for,
                            starts=["singleton_routes", "greedy_cheapest_insertion"], budget=budget)


def make_contexts(n_contexts: int = 2, n_customers: int = 6, seed: int = 7, strict: bool = True,
                  reference_free: bool = False, combination: bool = False) -> list[ValidationContext]:
    """Micro-contextos: instancias de `n_customers` clientes (el MIP completo cierra en
    segundos), alternando clientes uniformes y agrupados. Misma semántica de `strict`,
    `reference_free` y `combination` que en el CLSP."""
    probe = make_diversity_probe()
    combo = make_combination_probe(probe) if combination else None
    contexts = []
    for k in range(n_contexts):
        inst = pm.CVRPInstance.random(n_customers, Random(seed + k), route_size=3.0, clustered=k % 2 == 1)
        problem = pm.CVRPModel(inst)
        contexts.append(ValidationContext(
            problem=problem,
            instances=[inst],
            trivial_solutions=[SingletonRoutes().build(inst, Random(0))],
            baseline_constructor=greedy_start(problem),  # partidas de prueba: la trivial y la greedy
            reference_destruction=RandomRemoval(problem),
            reference_neighborhood=None if reference_free else RelocateNeighborhood(problem),
            mip_time_limit=10.0,
            max_moves_checked=30,
            require_improving_from_start=strict,
            diversity_probe=probe,
            combination=combo,
        ))
    return contexts


def starting_solution_example(n_customers: int = 6, seed: int = 11) -> str:
    """Texto para el prompt: una micro-instancia y su solución de partida (una ruta por cliente)."""
    inst = pm.CVRPInstance.random(n_customers, Random(seed), route_size=3.0)
    sol = SingletonRoutes().build(inst, Random(0))
    lines = [f"depósito en {inst.coords[0]}, capacidad Q = {inst.capacity:g}", "clientes (coordenadas, demanda):"]
    for c in inst.customers:
        lines.append(f"  {c}: {inst.coords[c]}  d={inst.demand[c]:g}")
    lines.append(f"solución de PARTIDA (una ruta por cliente): {sol}  distancia = {pm.CVRPModel(inst).objective(sol):.1f}")
    lines.append("Desde aquí, un movimiento MEJORA si junta clientes cercanos en una misma ruta sin exceder Q: p.ej. mover "
                 "un cliente al final de la ruta de un cliente cercano ahorra dist(0,c) + dist(c,0) y agrega un desvío menor. "
                 "Un movimiento que solo reordena dentro de una ruta de un cliente no cambia nada.")
    return "\n".join(lines)
