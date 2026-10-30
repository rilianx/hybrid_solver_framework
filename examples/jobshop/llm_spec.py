"""Descripción del job shop para la generación del modelo con LLM (§6.1), en sus dos representaciones."""

from __future__ import annotations

import inspect
from dataclasses import replace

FORBIDDEN = ["examples.jobshop.model_parts", "examples.jobshop.ops_parts", "examples.jobshop.components",
             "examples.jobshop.cases", "examples.jobshop.catalog"]


def make_model_spec():
    """La variante `sequences`: una secuencia de trabajos por máquina."""
    from llm.model_generator import ModelSpec

    from . import instance

    return ModelSpec(
        name="Job shop scheduling (makespan)",
        description=(
            "Hay `inst.n_jobs` trabajos y `inst.n_machines` máquinas. Cada trabajo j tiene una ruta `inst.routes[j]`: una "
            "secuencia de operaciones (máquina, tiempo de proceso) que se deben hacer en ese orden, cada una en su máquina, "
            "sin interrupción; la operación k+1 de un trabajo no puede empezar antes de que termine la k. Cada máquina "
            "procesa una operación a la vez. Cada trabajo pasa a lo sumo una vez por cada máquina. Una solución fija el orden "
            "de las operaciones en cada máquina, y el plan es el SEMIACTIVO: cada operación empieza apenas terminan la "
            "anterior de su trabajo y la anterior de su máquina. Objetivo: minimizar el makespan (el instante en que termina "
            "la última operación). Si los órdenes de las máquinas forman un ciclo con las rutas (A antes que B en una "
            "máquina y B antes que A, directa o indirectamente, en otra) no hay plan: la solución es infactible. Una "
            "solución infactible debe tener un objetivo finito pero peor que cualquier factible (penalización)."
        ),
        instance_source=inspect.getsource(instance.JSSPInstance),
        instance_import="examples.jobshop.instance",
        representation=("Una tupla con una secuencia por máquina (en el orden de las máquinas 0..m-1): la tupla de trabajos "
                        "en el orden en que esa máquina los procesa. Es la que usan los vecindarios clásicos del job shop "
                        "(intercambios en los bloques del camino crítico)."),
        forbidden_modules=FORBIDDEN,
        answer_format=("Una lista por máquina, en el orden de las máquinas 0..m-1; cada una, la lista de trabajos (enteros "
                       "desde 0) en el orden en que esa máquina los procesa. Ejemplo con 3 trabajos y 2 máquinas: "
                       "[[0, 2, 1], [2, 0, 1]]. El makespan es el del plan semiactivo de esos órdenes."),
        families=("Familias de restricciones: `secuencia` (cada máquina procesa exactamente una vez a cada trabajo que pasa "
                  "por ella; magnitud = trabajos que faltan, sobran o se repiten) y `orden` (los órdenes de las máquinas "
                  "no forman un ciclo con las rutas; magnitud > 0 si lo forman, p.ej. cuántas operaciones no se pueden "
                  "agendar). Término del objetivo: `makespan`."),
        notes=["En el MIP, el orden entre dos trabajos en una máquina se modela con binarias de precedencia y restricciones "
               "disyuntivas big-M sobre los inicios; M = suma de todos los tiempos de proceso (`inst.horizon()`) basta.",
               "Un ciclo de órdenes es una violación de la familia `orden`: en el MIP, ningún vector de inicios cumple a la "
               "vez las precedencias de las rutas y las disyuntivas de esas binarias (todo tiempo de proceso es >= 1)."],
    )


def make_ops_model_spec():
    """La variante `operations`: permutación con repetición (decodificador)."""
    return replace(
        make_model_spec(),
        name="Job shop scheduling (makespan) con permutación con repetición",
        representation=(
            "PERMUTACIÓN CON REPETICIÓN (Bierwirth): una tupla de trabajos en la que cada trabajo j aparece "
            "len(inst.routes[j]) veces; la k-ésima aparición de j es su operación k. Se decodifica recorriéndola y "
            "agregando cada operación al final de la secuencia de su máquina; las secuencias que resultan nunca forman un "
            "ciclo. violations y cost_terms se evalúan sobre esas secuencias. from_answer devuelve un orden de despacho "
            "de las secuencias de la respuesta (p.ej. sus operaciones ordenadas por inicio en el plan semiactivo); "
            "from_assignment, lo mismo con las secuencias que describen las binarias."
        ),
        decoder=True,
    )
