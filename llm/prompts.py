"""Construcción de prompts por slot (§6): el `Protocol` exacto, el bloque
`COMPONENT` obligatorio, un ejemplo válido para *otro* problema (few-shot),
la descripción del problema, y pedido explícito de diversidad. El prompt
de corrección reenvía el módulo original junto con el `feedback()` del
validador (la propiedad violada, con el movimiento/instancia concretos).
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field

from core import contracts
from core.validation.syntactic import PROTOCOL_FOR_SLOT

from .fewshot import FEWSHOT


@dataclass
class ProblemSpec:
    """Lo que el LLM necesita saber del problema para escribir componentes."""

    name: str
    description: str  # lenguaje natural: decisiones, restricciones, objetivo
    solution_representation: str  # cómo es `sol` en la vista estructural
    problem_model_import: str  # p.ej. "examples.lotsizing.problem_model"
    problem_model_source: str  # código fuente del ProblemModel (la vista que ve el componente)
    variable_naming: str  # cómo se llaman las variables de la vista MIP
    notes: list[str] = field(default_factory=list)  # avisos (minimización, penalización, costo de objective...)
    starting_solution: str | None = None  # micro-instancia + solución de partida, para slots que operan sobre ella


SYSTEM_PROMPT = """Eres un experto en metaheurísticas y matheurísticas que escribe componentes algorítmicos en Python.
Escribes módulos pequeños, correctos y autocontenidos que cumplen exactamente un contrato (Protocol) dado.
No escribes el bucle de control del algoritmo: solo la pieza que se te pide.

Reglas de todo módulo que generes:
1. Define un dict `COMPONENT` con: name (snake_case, único), slot, compatible_skeletons, requires, params.
   Cada param declara type ("int" | "float" | "cat" | "bool"), y range [min, max] para int/float o values [...] para cat.
2. Define una clase que implemente TODOS los métodos del Protocol del slot, con las firmas exactas.
3. Define `def build_component(problem, **params)` que devuelva una instancia lista para usar.
   `problem` es el ProblemModel ya ligado a una instancia (expone objective(sol), is_feasible(sol), to_assignment(sol),
   from_assignment(x), variable_groups(inst), y los atributos que muestre su código fuente, p.ej. `problem.inst`).
   Los valores por defecto de `build_component` deben caer dentro de los rangos declarados en COMPONENT["params"].
4. Solo imports de la librería estándar y del módulo del problema que se indica. Sin I/O, sin prints, sin estado global.
5. Toda aleatoriedad debe venir del `rng: random.Random` que recibe el método (nunca del módulo `random` global).
6. Las soluciones son inmutables: nunca modifiques `sol` in place; devuelve una solución nueva.
7. El objetivo se MINIMIZA en todo el framework.

Formato de salida: cada componente en su propio bloque ```python ... ``` con el módulo completo. Sin texto fuera de los bloques
salvo una línea breve antes de cada bloque. Nada más."""


def protocol_source(slot: str) -> str:
    return inspect.getsource(PROTOCOL_FOR_SLOT[slot])


SLOT_HINTS = {
    "neighborhood": (
        "Un movimiento `m` debe ser un objeto pequeño y hashable (tupla). Propiedades que se verificarán automáticamente: "
        "`undo(apply(sol, m), m) == sol` (cuidado con movimientos compuestos: la inversa debe restaurar TODAS las celdas tocadas); "
        "`delta(sol, m) == objective(apply(sol, m)) - objective(sol)` (puedes implementarlo literalmente así si no hay forma "
        "incremental barata); `moves(sol)` no vacío; y al menos un movimiento debe MEJORAR la solución de partida del esqueleto "
        "(no basta con que mejore soluciones aleatorias). Un vecindario con 6 movimientos que nunca mejoran es inútil aunque sea correcto. "
        "Además se mide si es una IDEA distinta de los vecindarios ya aceptados: se compara qué vecinos alcanza y, sobre todo, si sus "
        "movimientos que mejoran llegan a soluciones que los otros no alcanzan. Mezclar flips de un setup dentro de otro operador para "
        "que \"mejore\" no cuenta: esas mejoras ya las hace `setup_flip`."
    ),
    "constructor": (
        "Se verificará: `build(inst, rng)` devuelve una solución FACTIBLE y es determinista dada la semilla del rng. "
        "Factible significa cubrir TODA la demanda respetando la capacidad de cada período. Con utilización alta esto NO es "
        "trivial: lot-for-lot (setup justo donde hay demanda) puede exceder la capacidad de un período pico y dejar faltante, "
        "y entonces hay que producir ANTES y almacenar. Regla práctica: recorre los períodos en orden; si la demanda acumulada "
        "hasta t (más tiempos de setup) supera la capacidad acumulada disponible, adelanta producción a períodos anteriores con "
        "holgura. Comprueba la factibilidad con `problem.is_feasible(sol)` dentro de `build` y repara antes de devolver."
    ),
    "perturbation": "Se verificará: `perturb(sol, strength, rng)` devuelve una solución distinta de `sol` (para strength >= 1).",
    "destruction": (
        "`destroy(sol, ratio, rng)` devuelve `(partial, free_vars)`: `free_vars` es un set de NOMBRES de variables de la vista MIP "
        "(exactamente los que produce `problem.to_assignment(sol)`), y `partial` es el dict de las variables NO liberadas con su valor "
        "actual. Se verificará: free_vars ⊆ variables, partial ∪ free_vars = todas las variables, partial no toca variables liberadas, "
        "y |free_vars| >= 1."
    ),
    "acceptance": "Se verificará: una mejora estricta (f_cand < f_cur) siempre se acepta; devuelve bool.",
    "stop": "Se verificará: `stop(state)` es False en el estado inicial y True cuando iteration/elapsed_time son enormes.",
}


# Esqueletos del ensamblador que consumen cada slot: lo que el LLM debe declarar en
# COMPONENT["compatible_skeletons"] para que el componente entre al espacio de diseño
# de todos los esqueletos donde tiene sentido (no solo a los del ejemplo few-shot).
SKELETONS_FOR_SLOT = {
    "constructor": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
    "neighborhood": ["SA", "ILS", "TS", "VNS", "GRASP"],
    "perturbation": ["ILS"],
    "destruction": ["LNS_MIP"],
    "repair_mip": ["LNS_MIP"],
    "fixing_policy": ["FIX_OPT"],
    "acceptance": ["SA", "ILS", "LNS_MIP"],
    "stop": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
}


def generation_prompt(spec: ProblemSpec, slot: str, n_variants: int, avoid_names: list[str] | None = None) -> str:
    fewshot = FEWSHOT.get(slot)
    parts = [
        f"# Tarea\nGenera {n_variants} componentes ESTRUCTURALMENTE DISTINTOS para el slot `{slot}` del problema descrito abajo.",
        "Distintos significa ideas algorítmicas diferentes (no el mismo operador con otro parámetro). Nombra cada uno de forma descriptiva.",
        f"\n# Contrato del slot `{slot}` (Protocol exacto)\n```python\n{protocol_source(slot)}```",
    ]
    if slot in SLOT_HINTS:
        parts.append(f"\n# Propiedades que verificará el validador\n{SLOT_HINTS[slot]}")
    if slot in SKELETONS_FOR_SLOT:
        parts.append(
            f"\nDeclara `\"compatible_skeletons\": {SKELETONS_FOR_SLOT[slot]}` salvo que el componente dependa de un "
            "esqueleto concreto (p.ej. use la temperatura de SA)."
        )
    if fewshot:
        parts.append(
            "\n# Ejemplo de componente válido para OTRO problema (mochila 0/1), en el formato exacto requerido\n"
            f"```python{fewshot}```"
        )
    parts.append(f"\n# Problema objetivo: {spec.name}\n{spec.description}")
    parts.append(f"\n## Representación de la solución (vista estructural)\n{spec.solution_representation}")
    parts.append(f"\n## Variables de la vista MIP\n{spec.variable_naming}")
    parts.append(
        f"\n## Código del ProblemModel (lo que `problem` expone; importa tipos con `from {spec.problem_model_import} import ...`)\n"
        f"```python\n{spec.problem_model_source}\n```"
    )
    if spec.notes:
        parts.append("\n## Avisos\n" + "\n".join(f"- {n}" for n in spec.notes))
    if spec.starting_solution and slot in ("neighborhood", "perturbation"):
        parts.append(
            "\n## Desde dónde arranca el esqueleto (el validador exige que haya movimientos de mejora desde aquí)\n"
            f"```\n{spec.starting_solution}\n```"
        )
    if avoid_names:
        parts.append(f"\nYa existen componentes llamados {avoid_names}; usa ideas y nombres distintos.")
    parts.append(f"\nDevuelve exactamente {n_variants} bloques ```python```, cada uno un módulo completo.")
    return "\n".join(parts)


def correction_prompt(spec: ProblemSpec, slot: str, module_source: str, feedback: str) -> str:
    return "\n".join(
        [
            f"El siguiente componente para el slot `{slot}` del problema '{spec.name}' fue RECHAZADO por el validador automático.",
            "Corrígelo manteniendo la misma idea algorítmica y el mismo `COMPONENT['name']`. Devuelve el módulo completo corregido "
            "en un único bloque ```python```.",
            "Importante: arregla SOLO lo que el reporte señala y no rompas lo que ya pasaba. Si el problema es que el operador no "
            "mejora, NO agregues movimientos compuestos (dos setups a la vez, mover+quitar): mantén movimientos elementales con "
            "`undo` exacto y usa las pistas del reporte sobre qué movimientos concretos sí mejoran.",
            f"\n# Reporte del validador\n{feedback}",
            f"\n# Contrato del slot (Protocol exacto)\n```python\n{protocol_source(slot)}```",
            f"\n# Módulo rechazado\n```python\n{module_source}\n```",
            f"\n# Recordatorio del problema\n{spec.solution_representation}\n{spec.variable_naming}",
        ]
    )


__all__ = ["ProblemSpec", "SYSTEM_PROMPT", "generation_prompt", "correction_prompt", "protocol_source"]

_ = contracts  # el import explícito documenta de dónde salen los Protocols
