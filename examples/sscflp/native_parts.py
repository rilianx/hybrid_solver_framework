"""El SSCFLP en C++ con el modelo escrito por el LLM (`generated/sscflp_native/model/model.hpp`, o
`HSF_SSCFLP_NATIVE_MODEL`); ver `examples/lotsizing/native_parts.py`."""

from __future__ import annotations

import os

from native.generic_model import generation

MODEL_DIR = os.environ.get("HSF_SSCFLP_NATIVE_MODEL", "generated/sscflp_native/model")
GENERATION = generation(MODEL_DIR, "examples.sscflp.model_parts")
