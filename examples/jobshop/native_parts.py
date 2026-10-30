"""Las piezas del job shop (representación por secuencias) con la vista heurística y la constructiva en
C++ (`native/jobshop.hpp`) y la vista MIP de Python (`model_parts`).

Es la forma que tiene un modelo nativo para el framework: el validador lo prueba con los mismos casos
y capas que las piezas de Python (los casos son texto, no dependen del lenguaje), y los esqueletos
nativos lo corren sin pasar por Python (`solve`).
"""

from __future__ import annotations

from pathlib import Path

from native.build import load_module

from . import model_parts as _py
from .instance import JSSPInstance

SOURCE = Path(__file__).with_name("native") / "jobshop_py.cpp"
native = load_module("hsf_jobshop", SOURCE)

_MODELS: dict[JSSPInstance, object] = {}


def model(inst: JSSPInstance):
    """El modelo C++ de la instancia (uno por instancia, reutilizado)."""
    m = _MODELS.get(inst)
    if m is None:
        if len(_MODELS) > 256:
            _MODELS.clear()
        m = _MODELS[inst] = native.parse(inst.to_text())
    return m


def _seed(rng) -> int:
    return rng.getrandbits(63)


canonical = _py.canonical
from_answer = _py.from_answer


def trivial_solution(inst):
    return native.trivial_solution(model(inst))


def random_solution(inst, rng):
    return native.random_solution(model(inst), _seed(rng))


def violations(inst, sol):
    return native.violations(model(inst), sol)


def cost_terms(inst, sol):
    return native.cost_terms(model(inst), sol)


# ---------------------------------------------------------------- vista MIP (Python)
variables = _py.variables
structural_variables = _py.structural_variables
to_assignment = _py.to_assignment
aux_values = _py.aux_values
from_assignment = _py.from_assignment
constraint_families = _py.constraint_families
objective_terms = _py.objective_terms
variable_groups = _py.variable_groups


# ---------------------------------------------------------------- vista constructiva (C++)
def empty_partial(inst):
    return native.empty_partial(model(inst))


def candidates(inst, partial):
    return native.candidates(model(inst), partial)


def apply_action(inst, partial, action):
    return native.apply_action(model(inst), partial, action)


def is_complete(inst, partial) -> bool:
    return native.is_complete(model(inst), partial)


def to_solution(inst, partial):
    return native.to_solution(model(inst), partial)


def complete_partial(inst, partial, rng):
    return native.complete_partial(model(inst), partial, _seed(rng))
