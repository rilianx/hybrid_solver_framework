"""El PFSP con makespan en C++ con el modelo escrito por el LLM (`generated/flowshop_cmax_native/model/model.hpp`, o
`HSF_FLOWSHOP_CMAX_NATIVE_MODEL`); ver `examples/lotsizing/native_parts.py`."""

from __future__ import annotations

import os

from native.generic_model import generation

MODEL_DIR = os.environ.get("HSF_FLOWSHOP_CMAX_NATIVE_MODEL", "generated/flowshop_cmax_native/model")
GENERATION = generation(MODEL_DIR, "examples.flowshop_cmax.model_parts")
