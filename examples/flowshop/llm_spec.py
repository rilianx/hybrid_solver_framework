"""Lo que ve el LLM del flow shop de permutación con flowtime total (sin el modelo de referencia)."""

from __future__ import annotations

import inspect


def make_model_spec():
    from llm.model_generator import ModelSpec

    from . import instance

    return ModelSpec(
        name="Flow shop de permutación, flowtime total (PFSP-TFT)",
        description=(
            "Hay n trabajos y m máquinas. Todos los trabajos pasan por las máquinas en el mismo orden (0, 1, ..., m-1); el "
            "trabajo j ocupa la máquina i durante p[i][j]. Cada máquina procesa un trabajo a la vez y todas las máquinas "
            "procesan los trabajos en el MISMO orden (una permutación de los trabajos). Cada trabajo empieza en una máquina "
            "apenas terminó en la anterior y la máquina terminó el trabajo previo de la secuencia. Objetivo: minimizar el "
            "flowtime total, la suma de los instantes en que cada trabajo termina en la última máquina. Si la secuencia no es "
            "una permutación (faltan, sobran o hay trabajos que no existen) es infactible; su flowtime se calcula igual sobre "
            "la secuencia tal como viene, saltando los índices que no existen. Una solución infactible debe tener un objetivo "
            "finito pero peor que cualquier factible (penalización)."
        ),
        instance_source=inspect.getsource(instance.PFSPInstance),
        instance_import="examples.flowshop.instance",
        answer_format=("Una lista con UNA sola lista: el orden de los trabajos (enteros desde 0). Ejemplo con 4 trabajos: "
                       "[[2, 0, 3, 1]]."),
        families=("Familia de restricciones: `permutacion` (magnitud = trabajos que faltan + repeticiones de más + índices que "
                  "no existen). Término del costo: `flowtime`."),
    )
