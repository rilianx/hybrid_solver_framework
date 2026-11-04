"""Descripción del CLSP para el generador LLM del modelo nativo (`ModelSpec`)."""

from __future__ import annotations

import inspect


def make_model_spec():
    """Para generar el `ProblemModel` con LLM (§6.1): la descripción y la instancia, sin el modelo
    escrito a mano (`problem_model` queda prohibido; la instancia vive en `instance`)."""
    from core.model_spec import ModelSpec

    from . import instance

    return ModelSpec(
        name="Lot sizing capacitado multi-ítem (CLSP)",
        description=(
            "Hay `n_items` productos y `n_periods` períodos. Cada producto i tiene demanda d[i][t] por período, costo de setup "
            "s[i] (se paga en cada período en que el ítem tiene setup, produzca o no), costo de inventario h[i] por unidad "
            "almacenada al final de un período y tiempo de setup st[i]. Cada período t tiene capacidad cap[t] compartida: la "
            "producción x[i][t] de todos los ítems más los tiempos de setup de los ítems con setup en t no puede superar cap[t]. "
            "Un ítem solo puede producir en un período en que tiene setup. No hay backlog: la demanda de t se cubre con "
            "producción de t o con inventario de períodos anteriores; el inventario inicial es 0. Objetivo: minimizar el costo "
            "de setups más el de inventario."
        ),
        representation=(
            "El PLAN DE SETUPS (qué ítem tiene setup en qué período), como tupla de tuplas de bool de forma n_items × n_periods "
            "(la usan los componentes heurísticos del problema). Dado un plan, la producción se decide de forma óptima: producir "
            "lo más posible de la demanda respetando capacidades y, entre los planes que cubren lo máximo, el de menor inventario. "
            "Un plan de setups es factible si con él se cubre toda la demanda. Su costo es el de sus setups más el inventario de "
            "esa producción óptima."
        ),
        instance_source=inspect.getsource(instance.CLSPInstance),
        instance_import="examples.lotsizing.instance",
        notes=["La producción óptima dada un plan de setups es un LP: puedes resolverlo con PuLP (`import pulp`, solver "
               "`pulp.PULP_CBC_CMD(msg=False)`); conviene memorizar el resultado por (instancia, plan)."],
        forbidden_modules=["examples.lotsizing.problem_model", "examples.lotsizing.components", "examples.lotsizing.construction",
                           "examples.lotsizing.model_parts", "examples.lotsizing.cases", "examples.lotsizing.catalog"],
        construction=("Con tiempos de setup, decidir si un plan parcial se puede completar es difícil: filtra candidatos con una "
                      "condición necesaria barata (p.ej. que la capacidad libre acumulada hasta cada período alcance para la "
                      "demanda pendiente con deadline hasta ahí más los setups que faltan), y en un callejón sin salida "
                      "devuelve un plan factible seguro (con todos los setups encendidos lo es)."),
        answer_format=("Matriz de setups: lista de `n_items` listas de `n_periods` enteros 0/1; answer[i][t] = 1 si el ítem i "
                       "tiene setup en el período t. Ejemplo con 2 ítems y 3 períodos: [[1, 0, 1], [1, 1, 0]]."),
        families=("Familia de restricciones: `demanda` (magnitud = unidades de demanda que el plan de setups no alcanza a cubrir "
                  "con la producción óptima; la capacidad nunca se viola porque la producción la respeta). Términos del objetivo: "
                  "`setup` e `inventario`. En la vista MIP, además de `demanda` (balance de inventario), puede haber familias que "
                  "la producción óptima siempre cumple, como `capacidad` o el enlace producción-setup."),
    )
