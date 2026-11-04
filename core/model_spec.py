"""Lo que el LLM recibe de un problema para escribir su modelo (`llm.native_model_generator`): la descripción en
lenguaje natural, la clase de instancia, el formato de las respuestas de los casos y las familias de restricciones."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ModelSpec:
    """Lo que se le da al LLM para escribir el modelo."""

    name: str
    description: str  # datos, restricciones y objetivo, en lenguaje natural
    instance_source: str  # código de la clase de instancia
    instance_import: str  # módulo desde donde se importa la clase de instancia
    notes: list[str] = field(default_factory=list)
    # módulos que el generado no puede importar (p.ej. el modelo de referencia: sería copiarlo)
    forbidden_modules: list[str] = field(default_factory=list)
    # generación por piezas (`llm.parts_generator`): formato neutral de las respuestas de los casos y
    # nombres de las familias de restricciones y de los términos del objetivo
    answer_format: str = ""
    # cómo es `sol` en la vista heurística. Cada representación es un problema distinto para el framework
    # (su pack, sus componentes, su tuning); vacío = la elige el LLM. `decoder`: la representación es una
    # codificación que se decodifica a una solución (p.ej. gran tour + Split) y from_answer puede devolver
    # una codificación cuya decodificación sea igual o MEJOR que la respuesta del caso
    representation: str = ""
    decoder: bool = False
    # pista para la vista constructiva (etapa 3 de la generación por piezas), si el problema la necesita
    construction: str = ""
    families: str = ""
