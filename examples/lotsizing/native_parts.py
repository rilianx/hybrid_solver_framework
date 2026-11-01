"""El CLSP en C++ con el modelo escrito por el LLM (`llm.native_model_generator`, contrato genérico en
`native/include/hsf/generic.hpp`): no hay modelo C++ escrito a mano. `GENERATION` apunta al modelo generado del
workspace (`generated/clsp_native/model/model.hpp`, o `HSF_CLSP_NATIVE_MODEL`); sobre él se generan los componentes
C++ (`llm.native_generator`) y corren los esqueletos nativos (`--native --catalog generated`)."""

from __future__ import annotations

import os

from native.generic_model import generation

MODEL_DIR = os.environ.get("HSF_CLSP_NATIVE_MODEL", "generated/clsp_native/model")
GENERATION = generation(MODEL_DIR, "examples.lotsizing.model_parts")
