"""El CVRP en C++ con el modelo escrito por el LLM (`generated/cvrp_native/model/model.hpp`, o
`HSF_CVRP_NATIVE_MODEL`); ver `examples/lotsizing/native_parts.py`."""

from __future__ import annotations

import os

from native.generic_model import generation

MODEL_DIR = os.environ.get("HSF_CVRP_NATIVE_MODEL", "generated/cvrp_native/model")
GENERATION = generation(MODEL_DIR, "examples.cvrp.model_parts")
