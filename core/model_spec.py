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
    # módulos que el código generado no puede importar (el oráculo y los casos: sería copiarlos)
    forbidden_modules: list[str] = field(default_factory=list)
    # formato neutral de las respuestas de los casos y nombres de las familias de restricciones y de los términos del
    # objetivo (`families`)
    answer_format: str = ""
    families: str = ""
