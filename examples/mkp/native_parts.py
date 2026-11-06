"""El MKP en C++ con el modelo escrito por el LLM (`generated/mkp_native/model/model.hpp`, o
`HSF_MKP_NATIVE_MODEL`); ver `examples/lotsizing/native_parts.py`."""

from __future__ import annotations

import os

from native.generic_model import generation

MODEL_DIR = os.environ.get("HSF_MKP_NATIVE_MODEL", "generated/mkp_native/model")
GENERATION = generation(MODEL_DIR, "examples.mkp.model_parts")
