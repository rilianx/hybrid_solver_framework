"""Descripción del SSCFLP para la generación del modelo con LLM (`ModelSpec`)."""

from __future__ import annotations

import inspect

FORBIDDEN = ["examples.sscflp.model_parts", "examples.sscflp.cases", "examples.sscflp.best_known"]


def make_model_spec():
    from core.model_spec import ModelSpec

    from . import instance

    return ModelSpec(
        name="SSCFLP (localización de centros con capacidad y fuente única)",
        description=(
            "Hay `inst.n_facilities` centros candidatos y `inst.n_customers` clientes. El centro i tiene capacidad "
            "`inst.capacity[i]` y costo fijo de apertura `inst.fixed[i]`; el cliente j tiene demanda `inst.demand[j]`, "
            "y `inst.cost[i][j]` es el costo de atender TODA la demanda del cliente j desde el centro i. Cada cliente "
            "debe ser atendido por exactamente un centro (fuente única: su demanda no se divide). La suma de las "
            "demandas de los clientes asignados a un centro no puede superar su capacidad. Un centro está abierto si "
            "atiende a algún cliente y paga entonces su costo fijo; uno sin clientes está cerrado y no paga nada. "
            "Objetivo: minimizar la suma de los costos fijos de los centros abiertos más los costos de asignación. Una "
            "solución infactible debe tener un objetivo finito pero peor que cualquier factible (penalización). La "
            "solución trivial es: clientes de mayor a menor demanda (empates: menor índice), cada uno al centro con "
            "menor `cost[i][j]` (empates: menor índice) entre los que aún tienen capacidad libre para su demanda; si "
            "algún cliente no cabe, en su lugar first fit decreasing: clientes de mayor a menor demanda, cada uno al "
            "primer centro con capacidad libre recorriendo los centros de mayor a menor capacidad (empates: menor índice)."
        ),
        instance_source=inspect.getsource(instance.SSCFLPInstance),
        instance_import="examples.sscflp.instance",
        forbidden_modules=FORBIDDEN,
        answer_format=("Una lista con UNA sola lista de `inst.n_customers` enteros: en la posición j, el centro "
                       "(0..n_facilities-1) que atiende al cliente j, o -1 si el cliente no está atendido. Ejemplo con 4 "
                       "clientes y 3 centros: [[2, 0, 2, 2]] (abiertos los centros 0 y 2)."),
        families=("Familias de restricciones: `asignacion` (cada cliente atendido por exactamente un centro; magnitud = "
                  "clientes sin atender) y `capacidad` (magnitud = exceso total de demanda sobre la capacidad de los "
                  "centros). Términos del objetivo: `apertura` (costos fijos de los centros abiertos) y `transporte` "
                  "(costos de asignación)."),
    )
