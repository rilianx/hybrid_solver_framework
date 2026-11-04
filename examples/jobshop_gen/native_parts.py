"""El jobshop en C++ con el modelo escrito por el LLM (`generated/jobshop_gen_native/model/model.hpp`, o
`HSF_JOBSHOP_GEN_NATIVE_MODEL`); ver `examples/lotsizing/native_parts.py`."""

from __future__ import annotations

import os

from native.generic_model import generation

MODEL_DIR = os.environ.get("HSF_JOBSHOP_GEN_NATIVE_MODEL", "generated/jobshop_gen_native/model")
GENERATION = generation(MODEL_DIR, "examples.jobshop.model_parts")
