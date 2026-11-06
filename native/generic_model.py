"""Un modelo C++ escrito por el LLM (contrato en `native/include/hsf/generic.hpp`) visto como las piezas de Python.

La vista heurística (`trivial_solution`, `random_solution`, `violations`, `cost_terms`) sale del módulo C++; la forma
canónica, `from_answer` y la vista MIP, de las piezas de Python del problema (`mip_parts`): la representación del modelo
C++ es la forma de la respuesta, así que esas funciones no dependen de cómo esté escrito. Con esto el validador de los
modelos por piezas (`core.validation.model_parts`) lo prueba con los mismos casos, y los componentes C++ se generan y
corren sobre él (`generation(...)` es el `GENERATION` de `native.generated`).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

GENERIC_HEADER = "hsf/generic.hpp"


def generation(model_dir: str | Path, mip_parts: str) -> dict:
    """El `GENERATION` (ver `native.generated`) de un modelo generado en `model_dir/model.hpp`."""
    return {
        "dir": Path(model_dir),
        "model_header": "model.hpp",
        "bindings_header": GENERIC_HEADER,
        "namespace": "gen",
        "model_type": "gen::Model",
        "sol_to_py": "hsf::generic::sol_to_py",
        "sol_from_py": "hsf::generic::sol_from_py",
        "bind_problem": "hsf::generic::bind_problem<gen::Model>",
        "mip_parts": mip_parts,
    }


def model_parts(native, mip, model_of=None) -> SimpleNamespace:
    """Las piezas: vista heurística del módulo C++ `native` (forma canónica aplicada) y el resto de `mip`."""
    from native.generated import ModelCache

    model_of = model_of or ModelCache(native)
    canon = mip.canonical
    seed = lambda rng: rng.getrandbits(63)  # noqa: E731
    ns = SimpleNamespace(
        native=native, model=model_of, canonical=canon, from_answer=mip.from_answer,
        trivial_solution=lambda inst: canon(native.trivial_solution(model_of(inst))),
        random_solution=lambda inst, rng: canon(native.random_solution(model_of(inst), seed(rng))),
        # sin la forma canónica, para revisar la forma de lo que devuelve el modelo (`well_formed`): `canonical` puede
        # ocultar una forma equivocada (p.ej. quedarse con la primera fila)
        raw_trivial_solution=lambda inst: native.trivial_solution(model_of(inst)),
        raw_random_solution=lambda inst, rng: native.random_solution(model_of(inst), seed(rng)),
        violations=lambda inst, sol: native.violations(model_of(inst), sol),
        cost_terms=lambda inst, sol: native.cost_terms(model_of(inst), sol),
    )
    for name in ("well_formed", "variables", "structural_variables", "to_assignment", "aux_values", "from_assignment",
                 "constraint_families", "objective_terms", "variable_groups"):
        if hasattr(mip, name):
            setattr(ns, name, getattr(mip, name))
    return ns


__all__ = ["GENERIC_HEADER", "generation", "model_parts"]
