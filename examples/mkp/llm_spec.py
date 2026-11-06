"""Descripción de la mochila multidimensional para la generación del modelo con LLM (`ModelSpec`)."""

from __future__ import annotations

import inspect

FORBIDDEN = ["examples.mkp.model_parts", "examples.mkp.cases"]


def make_model_spec():
    from core.model_spec import ModelSpec

    from . import instance

    return ModelSpec(
        name="Mochila multidimensional (MKP, 0/1)",
        description=(
            "Hay `inst.n_items` ítems y `inst.n_resources` recursos. El ítem j da un beneficio `inst.profit[j]` y consume "
            "`inst.weight[i][j]` del recurso i; del recurso i hay `inst.capacity[i]` disponible. Una solución elige un "
            "subconjunto de ítems (cada uno a lo sumo una vez). Para cada recurso, el consumo total de los ítems "
            "elegidos no puede superar su capacidad. Objetivo: MAXIMIZAR el beneficio total de los ítems elegidos; como "
            "el framework minimiza, el objetivo es el beneficio total con signo menos. Una solución infactible debe "
            "tener un objetivo finito pero peor que cualquier factible (penalización). La solución trivial es la greedy "
            "(no la mochila vacía): se recorren los ítems por razón beneficio / Σ_i (consumo del recurso i / capacidad "
            "del recurso i) decreciente (empates: menor índice primero; si la suma es 0, la razón es infinita) y cada "
            "uno se agrega si cabe en todos los recursos con lo que queda libre."
        ),
        instance_source=inspect.getsource(instance.MKPInstance),
        instance_import="examples.mkp.instance",
        forbidden_modules=FORBIDDEN,
        answer_format=("Una lista con UNA sola lista de `inst.n_items` ceros y unos: en la posición j, 1 si el ítem j "
                       "está en la mochila. Ejemplo con 4 ítems: [[1, 0, 0, 1]] (elegidos los ítems 0 y 3)."),
        families=("Familia de restricciones: `capacidad` (el consumo de cada recurso no supera su capacidad; magnitud > 0 "
                  "si algún recurso se excede). Término del objetivo: `beneficio` (el beneficio total con signo menos)."),
    )
