"""El PFSP con flowtime total en C++ con el modelo escrito por el LLM (`generated/flowshop_native/model/model.hpp`, o
`HSF_FLOWSHOP_NATIVE_MODEL`); ver `examples/lotsizing/native_parts.py`."""

from __future__ import annotations

import os

from native.generic_model import generation

MODEL_DIR = os.environ.get("HSF_FLOWSHOP_NATIVE_MODEL", "generated/flowshop_native/model")
GENERATION = generation(MODEL_DIR, "examples.flowshop.model_parts")
