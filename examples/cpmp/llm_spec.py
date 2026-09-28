"""Descripción del CPMP para el generador LLM (§6) y micro-contextos de validación.

Solo el slot `greedy_score` tiene sentido todavía (no hay vecindarios ni vista MIP). El
prompt describe el problema y la vista constructiva neutral; no menciona FRG ni ninguna
otra heurística publicada, para que las ideas sean del modelo.
"""

from __future__ import annotations

import inspect
from random import Random

from core.validation import ValidationContext
from core.validation.base import DiversityProbe
from llm.prompts import ProblemSpec

from . import construction as c
from . import layout
from . import problem_model as pm
from .catalog import BestFirstConstructor
from .instance import CPMPInstance


def make_spec() -> ProblemSpec:
    return ProblemSpec(
        name="Container Pre-Marshalling Problem (CPMP)",
        description=(
            "Una bahía tiene S pilas de contenedores con altura máxima H. Cada contenedor tiene un grupo (entero >= 1; "
            "grupo mayor = se retira más tarde). Un movimiento saca el contenedor del tope de una pila y lo pone en el tope "
            "de otra que no esté llena. Una pila está ordenada si sus grupos no crecen de abajo hacia arriba. Un contenedor "
            "está bien puesto si está en el suelo o sobre un bien puesto de grupo mayor o igual; si no, está mal puesto. "
            "Objetivo: dejar todas las pilas ordenadas con la MENOR cantidad de movimientos."
        ),
        solution_representation=(
            "`sol` es una CPMPSolution con `moves`: tupla de (so, sd), mover el tope de la pila so a la sd, en orden desde "
            "el layout inicial. `problem.objective(sol)` es la cantidad de movimientos."
        ),
        problem_model_import="examples.cpmp.problem_model",
        problem_model_source=inspect.getsource(pm),
        variable_naming="El CPMP no tiene vista MIP en este framework: no uses to_assignment, from_assignment ni variable_groups.",
        notes=[
            "Cada mal puesto debe moverse al menos una vez: `partial.bad()` es una cota inferior de los movimientos que faltan.",
            "Un movimiento que deja bien puesto un contenedor mal puesto (sobre una pila ordenada con grupo del tope mayor o "
            "igual) es el único que avanza sin costo extra; los demás preparan espacio o desbloquean contenedores.",
            "Poner un contenedor sobre otro de grupo menor lo deja bloqueando: habrá que moverlo otra vez.",
        ],
        construction_source=_construction_source(),
        slot_hints={
            "greedy_score": (
                "En el CPMP: qué movimiento conviene hacer ahora. El estado parcial es el layout tras los movimientos hechos "
                "y la acción es Move(so, sd). Ideas distintas: qué contenedor sacar (mal puesto, desbloqueado, de grupo alto "
                "o bajo), dónde ponerlo (pila ordenada con grupo parecido, pila vacía, pila baja, pila ya desordenada), "
                "cuánto espacio libre queda, cuántos mal puestos se desbloquean. El puntaje se usa también dentro de una beam "
                "search, que completa cada candidato con el greedy de este mismo puntaje: un buen puntaje termina en pocos "
                "movimientos, no solo elige bien el siguiente. Cuidado: un puntaje miope (solo mira el movimiento siguiente) "
                "tiende a pasear los mismos mal puestos entre pilas desordenadas. `partial.moves` (los movimientos hechos) "
                "permite sostener un plan de varios pasos sin estado propio, y `partial.copy()` permite simular."),
        },
    )


def make_model_spec():
    """Para generar el `ProblemModel` con LLM (§6.1, `python -m llm.cycle model --problem cpmp --variant
    moves`): descripción, instancia y casos de prueba; sin vista MIP, con vista constructiva. No ve el
    modelo de referencia ni ninguna heurística."""
    from llm.model_generator import ModelSpec

    from . import instance

    return ModelSpec(
        name="Container Pre-Marshalling Problem (CPMP)",
        description=(
            "Una bahía tiene S pilas de contenedores con altura máxima H (`inst.stacks`: una tupla por pila con los grupos "
            "de sus contenedores, de abajo hacia arriba; `inst.H`, `inst.S`, `inst.N`, `inst.G` = grupo máximo). Grupo mayor = "
            "se retira más tarde. Un movimiento saca el contenedor del tope de una pila y lo pone en el tope de otra que no "
            "esté llena. Una pila está ordenada si sus grupos no crecen de abajo hacia arriba (cada contenedor está sobre uno "
            "de grupo mayor o igual). Una solución es una secuencia de movimientos que deja todas las pilas ordenadas. "
            "Objetivo: minimizar la cantidad de movimientos. Una solución con movimientos inválidos o que no ordena debe "
            "reportarse en `violations` (no rechazarse)."
        ),
        instance_source=inspect.getsource(instance.CPMPInstance),
        instance_import="examples.cpmp.instance",
        notes=["La representación de la solución la eliges tú; debe ser hashable y comparable con ==.",
               "`trivial_solution` tiene que ORDENAR el layout (no hay una solución factible sin movimientos en general): "
               "escribe un procedimiento simple que siempre termine en las micro-instancias."],
        forbidden_modules=["examples.cpmp.problem_model", "examples.cpmp.model_parts", "examples.cpmp.construction",
                           "examples.cpmp.layout", "examples.cpmp.frg", "examples.cpmp.catalog", "examples.cpmp.cases"],
        answer_format=("Lista de movimientos [so, sd] en orden, con índices de pila desde 0: mover el tope de la pila so a la "
                       "pila sd. Ejemplo: [[0, 2], [1, 0]]. [] es no mover nada."),
        families=("Familias de restricciones: `movimiento` (movimientos inválidos: origen vacío, destino lleno u origen = "
                  "destino; magnitud = cuántos; un movimiento inválido no se aplica) y `orden` (magnitud = contenedores mal "
                  "puestos en el layout final). Término del objetivo: `movimientos` (la cantidad de movimientos de la lista)."),
        mip=False,
        construction=("Una acción natural es un movimiento (so, sd). Una construcción que solo mueve contenedores puede "
                      "ciclar: evita volver a layouts ya recorridos y usa un tope de movimientos; complete_partial tiene que "
                      "ordenar el layout desde la parcial (o desde el inicial) con un procedimiento que siempre termine."),
    )


def _construction_source() -> str:
    return "\n\n".join(inspect.getsource(o) for o in (c.Move, layout.Layout)) + (
        "\n\n# Candidatos en cada paso: todos los Move(so, sd) válidos (so con contenedores, sd no llena, so != sd)\n"
        "# que no vuelven a un layout ya recorrido en esta construcción. Se termina cuando el layout está ordenado.\n"
        "# `score(partial, move)` elige cuál conviene; menor = mejor. No modifiques `partial`: usa sus consultas\n"
        "# (h, e, g, is_sorted_stack, ub, bad, stacks, sorted_n) o copia con partial.copy() si necesitas simular."
    )


def make_diversity_probe(S: int = 6, H: int = 6, seed: int = 100) -> DiversityProbe:
    inst = CPMPInstance.cvs_like(S, H, Random(seed))
    problem = pm.CPMPModel(inst)
    return DiversityProbe(problem=problem, solution=BestFirstConstructor(problem).build(inst, Random(0)), max_similarity=0.8)


def make_contexts(n_contexts: int = 2, seed: int = 7, strict: bool = True, reference_free: bool = False,
                  combination: bool = False) -> list[ValidationContext]:
    """Micro-contextos: instancias al estilo CVS de 4×4 y 5×4, donde el respaldo best-first
    siempre ordena. La sonda de tamaño realista (6×6) no se lo garantiza: ahí el greedy del
    puntaje tiene que terminar por sí mismo para ser factible. `strict`,
    `reference_free` y `combination` se aceptan por compatibilidad con los otros packs;
    no cambian nada aquí (no hay vecindarios)."""
    probe = make_diversity_probe()
    sizes = [(4, 4), (5, 4)]
    contexts = []
    for k in range(n_contexts):
        S, H = sizes[k % len(sizes)]
        inst = CPMPInstance.cvs_like(S, H, Random(seed + k))
        problem = pm.CPMPModel(inst)
        contexts.append(ValidationContext(
            problem=problem,
            instances=[inst],
            trivial_solutions=[BestFirstConstructor(problem).build(inst, Random(0))],
            baseline_constructor=BestFirstConstructor(problem),
            diversity_probe=probe,
        ))
    return contexts


__all__ = ["make_spec", "make_contexts", "make_diversity_probe"]
