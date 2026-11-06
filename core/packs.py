"""El pack de un problema a partir de sus piezas de referencia (`model_parts`): el `ProblemModel` (`PartsModel`), el
catálogo mínimo (partidas trivial y al azar), los contextos de validación de componentes y el registro de problemas."""

from __future__ import annotations

import importlib
from random import Random
from typing import Any

from core.model_parts import PartsModel
from core.problem_pack import ProblemPack

PACKS = {"clsp": "examples.lotsizing.pack", "cvrp": "examples.cvrp.pack", "jobshop": "examples.jobshop.pack",
         "flowshop": "examples.flowshop.pack", "flowshop_cmax": "examples.flowshop_cmax.pack",
         "sscflp": "examples.sscflp.pack"}


def base_pack(problem: str) -> ProblemPack:
    return importlib.import_module(PACKS[problem]).PACK


class TrivialConstructor:
    """La solución trivial de las piezas: partida de referencia y normalizador del tuner."""

    def __init__(self, parts):
        self.parts = parts

    def build(self, inst, rng: Random):
        return self.parts.trivial_solution(inst)


class RandomConstructor:
    def __init__(self, parts):
        self.parts = parts

    def build(self, inst, rng: Random):
        return self.parts.random_solution(inst, rng)


class _GroupDestruction:
    """Base de las destrucciones genéricas del sub-MIP de HYB: trabajan sobre la partición `variable_groups` de la
    vista MIP (en el CLSP, los setups de cada período), sin saber nada más del problema."""

    def __init__(self, problem):
        self.problem = problem
        self.groups = list(problem.variable_groups(problem.inst).values())

    def _split(self, sol, free: set[str]):
        x = self.problem.to_assignment(sol)
        return {v: x[v] for vs in self.groups for v in vs if v not in free}, free


class GroupWindowDestruction(_GroupDestruction):
    """Libera una ventana de grupos consecutivos (en el orden de `variable_groups`): `ratio` de los grupos, al menos
    uno. Con grupos por período es la destrucción por ventana de tiempo."""

    def destroy(self, sol, ratio: float, rng: Random):
        n = len(self.groups)
        width = max(1, min(n, round(ratio * n)))
        start = rng.randint(0, n - width)
        return self._split(sol, {v for g in self.groups[start:start + width] for v in g})


class RandomVariableDestruction(_GroupDestruction):
    """Libera una fracción `ratio` de las variables estructurales, al azar."""

    def destroy(self, sol, ratio: float, rng: Random):
        names = [v for g in self.groups for v in g]
        return self._split(sol, set(rng.sample(names, max(1, round(ratio * len(names))))))


def base_components(parts, skeletons: list[str]) -> list[tuple[dict, Any]]:
    """Los componentes genéricos del framework para unas piezas: partidas trivial y al azar y, si hay vista MIP, las
    destrucciones del sub-MIP de HYB."""
    out = [
        ({"name": "trivial", "slot": "constructor", "compatible_skeletons": skeletons, "params": {}},
         lambda problem: TrivialConstructor(parts)),
        ({"name": "random", "slot": "constructor", "compatible_skeletons": skeletons, "params": {}},
         lambda problem: RandomConstructor(parts)),
    ]
    if hasattr(parts, "variable_groups"):  # vista MIP: el sub-MIP de HYB tiene destrucciones genéricas
        out += [({"name": name, "slot": "destruction", "compatible_skeletons": ["HYB"], "params": {}}, cls)
                for name, cls in (("group_window", GroupWindowDestruction), ("random_variables", RandomVariableDestruction))]
    return out


def parts_contexts(base: ProblemPack, parts, n_contexts: int = 2, strict: bool = True, reference_free: bool = True,
                   combination: bool = False, pack: ProblemPack | None = None):
    from core.validation import ValidationContext
    from core.validation.base import DiversityProbe

    def good_start(problem, inst):
        """Partida con estructura: la mejor entre la trivial y unas al azar (la trivial sola puede ser
        degenerada: una ruta por cliente, corrida 20)."""
        cands = [parts.trivial_solution(inst)] + [parts.random_solution(inst, Random(s)) for s in range(8)]
        feas = [c for c in cands if problem.is_feasible(c)] or cands
        return min(feas, key=problem.objective)

    scale = base.make_instances(1, 100, base.parse_size(base.default_size))[0]
    probe_problem = PartsModel(parts, scale)
    probe = DiversityProbe(problem=probe_problem, solution=good_start(probe_problem, scale), max_similarity=0.8)
    combo = None
    if combination and pack is not None:
        combo = _combination_probe(pack, probe)
    micro = base.make_instances(n_contexts, 7, base.parse_size(base.micro_size or base.default_size))
    contexts = []
    for inst in micro:
        problem = PartsModel(parts, inst)
        contexts.append(ValidationContext(
            problem=problem,
            instances=[inst],
            trivial_solutions=[parts.trivial_solution(inst)],
            baseline_constructor=RandomConstructor(parts),
            mip_time_limit=10.0,
            max_moves_checked=30,
            require_improving_from_start=strict,
            diversity_probe=probe,
            combination=combo,
        ))
    return contexts


def _combination_probe(pack: ProblemPack, probe):
    from core.assembler import Assembler
    from core.component import ComponentSpec
    from core.validation.combination import CombinationProbe

    from core.catalog import build_registry

    def assembler_for(slot, components):
        registry = build_registry(pack, exclude_slots={slot})
        names = []
        for component, factory in components:
            spec = dict(component)
            spec.pop("combination_gains", None)
            registry.register(ComponentSpec.from_dict(spec, factory))
            names.append(spec["name"])
        assembler = Assembler(problem_factory=pack.problem_factory, registry=registry)
        assembler.probe_component = names[0]
        return assembler

    return CombinationProbe(instance=probe.problem.inst, assembler_for=assembler_for, starts=["trivial", "random"], budget=1.0)


# ------------------------------------------------------------------ vista MIP generada
def oracle_module(pack: ProblemPack):
    """Las piezas de referencia del problema (el oráculo humano: violaciones y costo)."""
    return importlib.import_module(pack.variants[next(iter(pack.variants))][1])


def mip_path(pack: ProblemPack, workspace: str | None = None):
    """El archivo de la vista MIP que escribió el LLM (`llm.native_mip_generator`), si existe."""
    from pathlib import Path

    path = Path(workspace or pack.default_workspace) / "mip" / "mip.py"
    return path if path.exists() else None


def load_mip(path) -> Any:
    """Importa una vista MIP generada desde su archivo (un nombre de módulo por contenido: dos versiones conviven)."""
    import hashlib
    import importlib.util
    import sys
    from pathlib import Path

    path = Path(path)
    name = "hsf_mip_" + hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except BaseException:
        del sys.modules[name]
        raise
    return mod


def with_mip(oracle, mip):
    """Las piezas del oráculo con la vista MIP de `mip` (las funciones de `core.model_parts.MIP_PARTS`)."""
    from types import SimpleNamespace

    from core.model_parts import MIP_PARTS

    ns = SimpleNamespace(**{k: getattr(oracle, k) for k in dir(oracle) if not k.startswith("__")})
    for name in MIP_PARTS:
        if hasattr(ns, name):
            delattr(ns, name)
        if hasattr(mip, name):
            setattr(ns, name, getattr(mip, name))
    ns.__name__ = f"{getattr(oracle, '__name__', 'parts')}+{getattr(mip, '__name__', 'mip')}"
    return ns


def with_generated_mip(pack: ProblemPack, mip_file) -> ProblemPack:
    """El pack con la vista MIP generada en lugar de la de referencia: el modelo de Python (el sub-MIP de HYB) y las
    destrucciones genéricas la usan; el oráculo sigue siendo el de referencia."""
    from dataclasses import replace

    parts = with_mip(oracle_module(pack), load_mip(mip_file))
    base = [(c, f) for c, f in pack.base_components if c["slot"] != "destruction"]
    base += [(c, f) for c, f in base_components(parts, list(pack.constructor_skeletons)) if c["slot"] == "destruction"]
    new = replace(pack, problem_factory=lambda inst: PartsModel(parts, inst), base_components=base)
    new.make_contexts = lambda n_contexts=2, strict=True, reference_free=True, combination=False: parts_contexts(
        new, parts, n_contexts, strict, reference_free, combination, new)
    return new


def parts_pack(base: ProblemPack, parts, parts_import: str, model_spec, name: str) -> ProblemPack:
    """El pack de una representación: instancias y casos del pack base; modelo, catálogo mínimo y
    especificación para los componentes, de las piezas."""
    pack = ProblemPack(
        name=name,
        module=base.module,
        problem_factory=lambda inst: PartsModel(parts, inst),
        base_components=base_components(parts, list(base.constructor_skeletons)),
        make_contexts=lambda **kw: None,  # se reemplaza abajo (necesita el pack para la sonda de combinación)
        make_instances=base.make_instances,
        parse_size=base.parse_size,
        default_size=base.default_size,
        baseline_constructor=lambda: TrivialConstructor(parts),
        load_instance=base.load_instance,
        make_model_spec=lambda: model_spec,
        micro_size=base.micro_size,
        load_cases=base.load_cases,
        constructor_skeletons=list(base.constructor_skeletons),
    )
    pack.make_contexts = lambda n_contexts=2, strict=True, reference_free=True, combination=False: parts_contexts(
        base, parts, n_contexts, strict, reference_free, combination, pack)
    return pack
