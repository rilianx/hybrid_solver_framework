"""Un `ProblemPack` armado a partir de un `ProblemModel` GENERADO por piezas (`llm.parts_generator`).

Cierra el ciclo de §6.1: descripción + casos → modelo generado → componentes generados →
tuning, sin nada escrito a mano del problema salvo la clase de instancia, su generador y los
casos (la entrada que da quien plantea el problema).

    pack = pack_from_generated_model(PACK, "generated/cpmp_model/problem_model/model_constructive_r1.py")

Del pack base solo se toman la instancia (generador, lector, tamaños) y los casos de prueba.
El catálogo de referencia NO se usa: sus componentes están escritos para la representación
del modelo de referencia, no la del generado. El catálogo queda con la partida trivial del
modelo (`trivial_solution`); lo demás lo genera el LLM (`--slots greedy_score`, y los slots
de búsqueda si el modelo tiene vista MIP). Sin vista MIP el único esqueleto es `CONSTRUCT`.

El módulo generado se registra en `sys.modules` como `generated_models.<pack>`, para que los
componentes que genere el LLM puedan importarlo.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path
from random import Random
from typing import Any

from core.model_parts import MIP_PARTS, PartsModel
from core.problem_pack import ProblemPack


class TrivialConstructor:
    """La partida trivial del modelo generado (`trivial_solution`), como constructor."""

    def __init__(self, parts: Any, problem: Any = None):
        self.parts, self.problem = parts, problem

    def build(self, inst, rng: Random):
        return self.parts.trivial_solution(inst)


def load_generated_model(path: str | Path, name: str):
    path = Path(path)
    mod_name = f"generated_models.{name}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("generated_models", type(sys)("generated_models"))
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


def pack_from_generated_model(base: ProblemPack, model_path: str | Path, n_contexts: int = 2) -> ProblemPack:
    if base.make_model_spec is None or base.load_cases is None:
        raise ValueError(f"el pack {base.name} no trae make_model_spec y load_cases: no hay con qué validar el modelo")
    name = f"{base.name}_gen"
    parts = load_generated_model(model_path, name)
    source = Path(model_path).read_text()
    model_spec = base.make_model_spec()
    has_mip = all(callable(getattr(parts, n, None)) for n in MIP_PARTS)
    has_view = callable(getattr(parts, "construction_view", None))
    skeletons = None if has_mip else ["CONSTRUCT"]
    constructor_skeletons = list(base.constructor_skeletons) + (["CONSTRUCT"] if has_mip else [])
    if not has_mip:
        constructor_skeletons = ["CONSTRUCT"]

    def problem_factory(inst):
        return PartsModel(parts, inst)

    def make_spec():
        from llm.prompts import ProblemSpec

        return ProblemSpec(
            name=model_spec.name,
            description=model_spec.description,
            solution_representation=("La representación de `sol` es la del modelo generado (ver `canonical`, `from_answer` y "
                                     "`construction_view` en su código). `problem.objective(sol)` es la suma de `cost_terms` "
                                     "más una penalización por las violaciones; `problem.is_feasible(sol)`, que no haya "
                                     "violaciones; `problem.inst` es la instancia."),
            problem_model_import=f"generated_models.{name}",
            problem_model_source=source,
            variable_naming=("Ver `variables` y `variable_groups` en el código del modelo." if has_mip else
                             "Este modelo no tiene vista MIP: no uses to_assignment, from_assignment ni variable_groups."),
            notes=list(model_spec.notes),
            construction_source=(("El estado parcial y las acciones son los de `construction_view(inst)` en el código del modelo "
                                  "(arriba): `score(partial, action)` recibe un parcial de esa vista y una de sus acciones.")
                                 if has_view else None),
            slot_hints={"greedy_score": model_spec.construction_notes} if model_spec.construction_notes else {},
        )

    def make_contexts(n_contexts: int = n_contexts, strict: bool = True, reference_free: bool = True,
                      combination: bool = False, **_):
        from core.validation import ValidationContext
        from core.validation.base import DiversityProbe

        cases = [c for c in base.load_cases() if c.solutions]
        cases = sorted(cases, key=lambda c: -(c.optimum or 0))[:n_contexts]  # los menos triviales
        probe_inst = base.make_instances(1, 777, base.parse_size(base.default_size))[0]
        probe_P = problem_factory(probe_inst)
        probe = DiversityProbe(problem=probe_P, solution=parts.trivial_solution(probe_inst), max_similarity=0.8)
        out = []
        for c in cases:
            P = problem_factory(c.instance)
            out.append(ValidationContext(problem=P, instances=[c.instance], trivial_solutions=[parts.trivial_solution(c.instance)],
                                         baseline_constructor=TrivialConstructor(parts, P), diversity_probe=probe,
                                         require_improving_from_start=strict))
        return out

    handwritten = [({"name": "trivial", "slot": "constructor", "compatible_skeletons": constructor_skeletons, "params": {}},
                    lambda problem: TrivialConstructor(parts, problem))]
    return replace(
        base,
        name=name,
        problem_factory=problem_factory,
        handwritten=handwritten,
        make_spec=make_spec,
        make_contexts=make_contexts,
        baseline_constructor=lambda: TrivialConstructor(parts),
        constructor_skeletons=constructor_skeletons,
        beam_constructors=has_view,
        skeletons=skeletons,
    )


__all__ = ["TrivialConstructor", "load_generated_model", "pack_from_generated_model"]
