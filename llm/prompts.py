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
    construction_source: str | None = None  # vista constructiva (estado parcial y acción), para el slot greedy_score
    # pistas propias del problema por slot, que se agregan a las genéricas de `SLOT_HINTS`
    slot_hints: dict[str, str] = field(default_factory=dict)


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


def slot_hint(spec: "ProblemSpec", slot: str) -> str:
    """Pista genérica del slot más la propia del problema, si la hay."""
    return " ".join(h for h in (SLOT_HINTS.get(slot, ""), spec.slot_hints.get(slot, "")) if h)


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
        "movimientos que mejoran llegan a soluciones que los otros no alcanzan. "
        "Los esqueletos no recorren `moves` completo: toman movimientos al azar o muestras. Si enumerar `moves(sol)` es caro, "
        "puedes agregar `sample(self, sol, k, rng) -> list` con hasta k movimientos DISTINTOS de `moves(sol)` elegidos con `rng` "
        "(se verifica); si no, no hace falta."
    ),
    "constructor": (
        "Se verificará: `build(inst, rng)` devuelve una solución FACTIBLE y es determinista dada la semilla del rng, "
        "también en una instancia de tamaño realista. Comprueba la factibilidad con `problem.is_feasible(sol)` dentro de "
        "`build` y repara antes de devolver."
    ),
    "perturbation": "Se verificará: `perturb(sol, strength, rng)` devuelve una solución distinta de `sol` (para strength >= 1).",
    "greedy_score": (
        "Escribes SOLO el criterio de un constructor greedy: `score(partial, action)` devuelve un número, MENOR es mejor. "
        "El bucle, la regla de selección (greedy, lista restringida de GRASP o ruleta) y la factibilidad son del framework: "
        "los candidatos ya vienen filtrados, así que el puntaje no tiene que comprobar capacidad ni reparar nada. "
        "Se llama para cada candidato en cada paso de la construcción, así que debe ser BARATO: usa los datos de la "
        "instancia y los atributos del parcial, nunca `problem.objective` ni `problem.is_feasible`. Se verificará: devuelve "
        "un número finito, es determinista, NO modifica `partial` (solo lo lee), y el constructor greedy que arma produce "
        "soluciones factibles y no mucho peores que la de referencia. Distintos puntajes = distintas ideas sobre qué conviene "
        "elegir primero (costo, urgencia, holgura, balance...)."
    ),
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
    "constructor": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "greedy_score": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "neighborhood": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "perturbation": ["ILS"],
    "destruction": ["LNS_MIP", "MIP_PERTURB"],
    "repair_mip": ["LNS_MIP"],
    "fixing_policy": ["FIX_OPT"],
    "acceptance": ["SA", "ILS", "LNS_MIP"],
    "stop": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH"],
}


def generation_prompt(spec: ProblemSpec, slot: str, n_variants: int, avoid_names: list[str] | None = None,
                      idea: "Idea | None" = None, avoid_ideas: bool = True) -> str:
    """Con `idea` (generación con planificador) pide UN módulo que implemente esa idea y no otra."""
    fewshot = FEWSHOT.get(slot)
    if idea is not None:
        task = [
            f"# Tarea\nImplementa UN componente para el slot `{slot}` del problema descrito abajo, siguiendo EXACTAMENTE esta idea:",
            f"\n**{idea.name}**: {idea.text}",
            f"\nUsa `COMPONENT[\"name\"] = \"{idea.name}\"`. No reemplaces la idea por otra más fácil: si no mejora, el "
            "validador te lo dirá y podrás corregir la implementación.",
        ]
        n_variants = 1
    else:
        task = [
            f"# Tarea\nGenera {n_variants} componentes ESTRUCTURALMENTE DISTINTOS para el slot `{slot}` del problema descrito abajo.",
            "Distintos significa ideas algorítmicas diferentes (no el mismo operador con otro parámetro). Nombra cada uno de forma descriptiva.",
        ]
    parts = task + [f"\n# Contrato del slot `{slot}` (Protocol exacto)\n```python\n{protocol_source(slot)}```"]
    if slot in SLOT_HINTS or slot in spec.slot_hints:
        parts.append("\n# Propiedades que verificará el validador\n" + slot_hint(spec, slot))
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
    if spec.construction_source and slot == "greedy_score":
        parts.append("\n## Vista constructiva: el estado parcial y la acción que recibe `score`\n"
                     f"```python\n{spec.construction_source}\n```")
    if spec.starting_solution and slot in ("neighborhood", "perturbation"):
        parts.append(
            "\n## Desde dónde arranca el esqueleto (el validador exige que haya movimientos de mejora desde aquí)\n"
            f"```\n{spec.starting_solution}\n```"
        )
    if avoid_names and not avoid_ideas:
        parts.append(f"\nYa existen componentes llamados {avoid_names}; usa nombres distintos. Puedes partir de las mismas "
                     "ideas si crees que las mejoras: los dos quedan en el catálogo y el tuner elige.")
    elif avoid_names:
        parts.append(f"\nYa existen componentes llamados {avoid_names}; usa ideas y nombres distintos.")
        if slot == "neighborhood":
            parts.append("Mezclar movimientos de un vecindario que ya existe dentro de otro operador para que \"mejore\" no "
                         "cuenta como idea nueva: esas mejoras ya las hace el existente.")
    parts.append(f"\nDevuelve exactamente {n_variants} bloques ```python```, cada uno un módulo completo.")
    return "\n".join(parts)


@dataclass
class Idea:
    """Una idea de componente propuesta por el planificador: nombre snake_case y 2–4 frases."""

    name: str
    text: str


def planning_prompt(spec: ProblemSpec, slot: str, n_ideas: int, avoid_names: list[str] | None = None,
                    accepted: list[Idea] | None = None, rejected: list[tuple[Idea, str]] | None = None,
                    avoid_ideas: bool = True) -> str:
    """El planificador propone ideas en texto, sin código: la diversidad se decide aquí, antes
    de gastar una implementación en algo que el gate de diversidad rechazaría después.

    `accepted` / `rejected` son las ideas de una ronda anterior (replaneo): las aceptadas no se
    repiten y las rechazadas vienen con el motivo (duplicado de otra, o no se logró implementar)."""
    parts = [
        f"# Tarea\nPropón {n_ideas} ideas ESTRUCTURALMENTE DISTINTAS de componente para el slot `{slot}` del problema de abajo. "
        "No escribas código: cada idea la implementará después otra persona, por separado y sin ver las demás.",
        "Cada idea: qué hace el operador en términos del problema, por qué debería mejorar las soluciones desde donde "
        "arranca el esqueleto, y en qué se diferencia de las otras. Distintas significa ideas algorítmicas diferentes, "
        "no el mismo operador con otro parámetro ni uno contenido en otro.",
        f"\n# Contrato del slot `{slot}` (lo que tendrá que implementar cada idea)\n```python\n{protocol_source(slot)}```",
    ]
    if slot in SLOT_HINTS or slot in spec.slot_hints:
        parts.append("\n# Propiedades que verificará el validador\n" + slot_hint(spec, slot))
    parts.append(f"\n# Problema: {spec.name}\n{spec.description}")
    parts.append(f"\n## Representación de la solución\n{spec.solution_representation}")
    if spec.notes:
        parts.append("\n## Avisos\n" + "\n".join(f"- {n}" for n in spec.notes))
    if spec.construction_source and slot == "greedy_score":
        parts.append(f"\n## Vista constructiva (estado parcial y acción)\n```python\n{spec.construction_source}\n```")
    if spec.starting_solution and slot in ("neighborhood", "perturbation"):
        parts.append(f"\n## Desde dónde arranca el esqueleto\n```\n{spec.starting_solution}\n```")
    if avoid_names and not avoid_ideas:
        parts.append(f"\nYa existen componentes llamados {avoid_names}; usa nombres distintos (las ideas pueden mejorar las suyas).")
    elif avoid_names:
        parts.append(f"\nYa existen componentes llamados {avoid_names}; propone ideas y nombres distintos.")
    if accepted:
        parts.append("\n## Ideas ya aceptadas (no las repitas ni propongas variantes de ellas)\n"
                     + "\n".join(f"- {i.name}: {i.text}" for i in accepted))
    if rejected:
        parts.append("\n## Ideas descartadas en la ronda anterior, con el motivo\n"
                     + "\n".join(f"- {i.name}: {i.text} → {why}" for i, why in rejected))
    parts.append(
        f"\nDevuelve SOLO un bloque ```json``` con una lista de {n_ideas} objetos "
        '`{"name": "<snake_case único>", "idea": "<2 a 4 frases>"}`.'
    )
    return "\n".join(parts)


def parse_ideas(text: str, n_max: int | None = None) -> list[Idea]:
    """Extrae la lista JSON de ideas (tolera texto alrededor y bloques sin etiqueta); nombres
    normalizados a snake_case y sin repetir."""
    import json
    import re

    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.S) or re.search(r"(\[\s*\{.*\}\s*\])", text, re.S)
    if not m:
        return []
    raw = m.group(1)
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        # Comas finales antes de `}` o `]` (corrida 12: el plan de constructores traía tres
        # ideas válidas con `"...",\n  }` y el slot terminó sin ninguna).
        try:
            items = json.loads(re.sub(r",\s*([}\]])", r"\1", raw))
        except json.JSONDecodeError:
            return []
    out, seen = [], set()
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict):
            continue
        name = re.sub(r"[^a-z0-9_]+", "_", str(it.get("name", "")).strip().lower()).strip("_")
        text_ = str(it.get("idea") or it.get("description") or "").strip()
        if not name or not text_ or name in seen:
            continue
        seen.add(name)
        out.append(Idea(name, text_))
    return out[:n_max] if n_max else out


def correction_prompt(spec: ProblemSpec, slot: str, module_source: str, feedback: str, idea: Idea | None = None) -> str:
    pinned = ([f"La idea que este componente debe implementar, y que NO debes cambiar por otra: **{idea.name}**: {idea.text}"]
              if idea is not None else [])
    return "\n".join(
        [
            f"El siguiente componente para el slot `{slot}` del problema '{spec.name}' fue RECHAZADO por el validador automático.",
            "Corrígelo manteniendo la misma idea algorítmica y el mismo `COMPONENT['name']`. Devuelve el módulo completo corregido "
            "en un único bloque ```python```.",
            *pinned,
            "Importante: arregla SOLO lo que el reporte señala y no rompas lo que ya pasaba. Si el problema es que el operador no "
            "mejora, NO agregues movimientos compuestos (dos cambios a la vez, mover+quitar): mantén movimientos elementales con "
            "`undo` exacto y usa las pistas del reporte sobre qué movimientos concretos sí mejoran.",
            f"\n# Reporte del validador\n{feedback}",
            f"\n# Contrato del slot (Protocol exacto)\n```python\n{protocol_source(slot)}```",
            f"\n# Módulo rechazado\n```python\n{module_source}\n```",
            f"\n# Recordatorio del problema\n{spec.solution_representation}\n{spec.variable_naming}",
        ]
    )


__all__ = ["Idea", "ProblemSpec", "SYSTEM_PROMPT", "correction_prompt", "generation_prompt", "parse_ideas",
           "planning_prompt", "protocol_source"]

_ = contracts  # el import explícito documenta de dónde salen los Protocols
