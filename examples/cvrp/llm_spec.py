"""Descripción del CVRP para el generador LLM del modelo nativo (`ModelSpec`)."""

from __future__ import annotations

import inspect

FORBIDDEN = ["examples.cvrp.model_parts", "examples.cvrp.cases"]


def make_model_spec():
    """Para generar el `ProblemModel` completo con LLM (§6.1): la descripción y la instancia, sin
    el modelo de referencia."""
    from core.model_spec import ModelSpec

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
        forbidden_modules=FORBIDDEN,
        answer_format=("Lista de rutas; cada ruta, una lista de clientes (enteros 1..n) en orden de visita, sin el depósito. "
                       "Ejemplo: [[3, 1], [2, 4]]. Dos respuestas con las mismas rutas en otro orden de rutas son la misma solución."),
        families=("Familias de restricciones: `visita` (cada cliente exactamente una vez; magnitud = cuántas visitas sobran o "
                  "faltan) y `capacidad` (magnitud = exceso de carga total). Término del objetivo: `distancia`."),
    )

