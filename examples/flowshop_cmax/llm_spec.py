"""Lo que ve el LLM del flow shop de permutación con makespan (sin el modelo de referencia)."""

from __future__ import annotations

import inspect


def make_model_spec():
    from core.model_spec import ModelSpec

    from examples.flowshop import instance

    return ModelSpec(
        name="Flow shop de permutación, makespan (PFSP-Cmax)",
        description=(
            "Hay n trabajos y m máquinas. Todos los trabajos pasan por las máquinas en el mismo orden (0, 1, ..., m-1); el "
            "trabajo j ocupa la máquina i durante p[i][j]. Cada máquina procesa un trabajo a la vez y todas las máquinas "
            "procesan los trabajos en el MISMO orden (una permutación de los trabajos). Cada trabajo empieza en una máquina "
            "apenas terminó en la anterior y la máquina terminó el trabajo previo de la secuencia. Objetivo: minimizar el "
            "makespan, el instante en que el último trabajo de la secuencia termina en la última máquina. Si la secuencia no es "
            "una permutación (faltan, sobran o hay trabajos que no existen) es infactible; su makespan se calcula igual sobre "
            "la secuencia tal como viene, saltando los índices que no existen. Una solución infactible debe tener un objetivo "
            "finito pero peor que cualquier factible (penalización)."
        ),
        instance_source=inspect.getsource(instance.PFSPInstance),
        instance_import="examples.flowshop.instance",
        answer_format=("Una lista con UNA sola lista: el orden de los trabajos (enteros desde 0). Ejemplo con 4 trabajos: "
                       "[[2, 0, 3, 1]]."),
        families=("Familia de restricciones: `permutacion` (magnitud = trabajos que faltan + repeticiones de más + índices que "
                  "no existen). Término del costo: `makespan`."),
    )
