"""El ciclo completo: de la descripción del problema y sus casos de prueba a un solver afinado,
sin nada escrito a mano salvo el generador de instancias y los casos.

    python -m llm.cycle model      --problem cvrp --variant tour --workspace generated/cvrp_tour_cycle
    python -m llm.cycle components --problem cvrp --variant tour --workspace generated/cvrp_tour_cycle
    python -m llm.cycle tune       --problem cvrp --variant tour --workspace generated/cvrp_tour_cycle -- --trials 40 ...

1. `model`: genera el `ProblemModel` por piezas (`llm.parts_generator`) con la representación de
   la variante y lo deja en `<workspace>/model/parts.py`.
2. `components`: genera los componentes DESDE CERO sobre ese modelo (`llm.cli`, `--from-scratch`):
   el LLM ve el código de las piezas, no un modelo escrito a mano.
3. `tune`: afina sobre el catálogo generado (`tuning.cli`).

Cada representación es un problema distinto: su pack se arma aquí (`parts_pack`) a partir del
pack base del problema (instancias, casos) y de las piezas. Con `--reference` se usan las piezas
de referencia de la variante en vez de las generadas (para separar los errores del modelo de los
de los componentes).

El slot `greedy_score` necesita una vista constructiva que un modelo por piezas no tiene: el
ciclo genera constructores completos (`constructor`), vecindarios, perturbaciones y destrucciones.
Como partidas de referencia quedan la solución trivial y la al azar del propio modelo.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import shutil
import sys
from dataclasses import replace
from pathlib import Path
from random import Random
from typing import Any

from core.model_parts import PartsModel
from core.problem_pack import ProblemPack

CYCLE_SLOTS = ["constructor", "neighborhood", "perturbation", "destruction"]
LOCAL_SEARCH_SKELETONS = ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"]


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


def _handwritten(parts, skeletons: list[str]) -> list[tuple[dict, Any]]:
    from core.fixing_policies import SlidingWindowPolicy

    return [
        ({"name": "trivial", "slot": "constructor", "compatible_skeletons": skeletons, "params": {}},
         lambda problem: TrivialConstructor(parts)),
        ({"name": "random", "slot": "constructor", "compatible_skeletons": skeletons, "params": {}},
         lambda problem: RandomConstructor(parts)),
        ({"name": "sliding_window", "slot": "fixing_policy", "compatible_skeletons": ["FIX_OPT"],
          "params": {"window_size": {"type": "int", "range": [1, 4]}, "overlap": {"type": "int", "range": [0, 2]}}},
         lambda problem, window_size=2, overlap=1: SlidingWindowPolicy(window_size, min(overlap, window_size - 1))),
    ]


PARTS_MODEL_API = '''
# El ProblemModel que recibe cada componente (`problem`) es PartsModel(piezas, inst):
#   problem.inst                     la instancia
#   problem.parts                    el módulo de piezas de arriba (canonical, violations, cost_terms, ...)
#   problem.objective(sol)           costo total + penalización por violaciones (se MINIMIZA)
#   problem.violations(sol)          {familia: magnitud > 0} de las violadas; {} si es factible
#   problem.is_feasible(sol)
#   problem.random_solution(rng)     una solución al azar con estructura válida
#   problem.to_assignment(sol)       {variable estructural: 0/1}
#   problem.from_assignment(x)       inversa (para destrucciones / sub-MIPs)
#   problem.variable_groups(inst)    {grupo: [variables estructurales]}
# Construye las soluciones que devuelvas con `canonical(...)` del módulo de piezas.
'''


def parts_problem_spec(model_spec, parts_import: str, parts_source: str):
    from llm.prompts import ProblemSpec

    return ProblemSpec(
        name=model_spec.name,
        description=model_spec.description,
        solution_representation=(model_spec.representation or "La de las piezas de abajo (ver canonical y random_solution).")
        + " Importa `canonical` y lo que necesites del módulo del problema indicado.",
        problem_model_import=parts_import,
        problem_model_source=parts_source + "\n" + PARTS_MODEL_API,
        variable_naming=("Las variables de la vista MIP son las de `structural_variables(inst)` en las piezas; "
                         "`variable_groups(inst)` las agrupa para Fix-and-Optimize."),
        notes=list(model_spec.notes),
    )


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

    from .catalog import build_registry

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


def parts_pack(base: ProblemPack, parts, parts_import: str, model_spec, name: str) -> ProblemPack:
    """El pack de una representación: instancias y casos del pack base; modelo, catálogo mínimo y
    especificación para los componentes, de las piezas."""
    source = inspect.getsource(parts)
    pack = ProblemPack(
        name=name,
        module="llm.cycle",
        problem_factory=lambda inst: PartsModel(parts, inst),
        handwritten=_handwritten(parts, list(base.constructor_skeletons)),
        make_spec=lambda: parts_problem_spec(model_spec, parts_import, source),
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


def base_pack(problem: str) -> ProblemPack:
    module = {"clsp": "examples.lotsizing.pack", "cvrp": "examples.cvrp.pack"}[problem]
    return importlib.import_module(module).PACK


def model_path(workspace: str | Path) -> Path:
    return Path(workspace) / "model" / "parts.py"


def import_name(path: Path) -> str:
    """Nombre importable de un archivo bajo el directorio de trabajo (paquetes implícitos)."""
    rel = path.resolve().relative_to(Path.cwd().resolve()).with_suffix("")
    if not all(p.isidentifier() for p in rel.parts):
        raise SystemExit(f"{path}: el workspace debe tener nombres de directorio válidos como identificadores de Python")
    return ".".join(rel.parts)


def load_variant(problem: str, variant: str, workspace: str | Path | None, reference: bool) -> ProblemPack:
    base = base_pack(problem)
    if variant not in base.variants:
        raise SystemExit(f"variante desconocida {variant!r} para {problem}: {sorted(base.variants)}")
    make_spec, ref_import = base.variants[variant]
    spec = make_spec()
    if reference:
        parts_import = ref_import
    else:
        path = model_path(workspace)
        if not path.exists():
            raise SystemExit(f"no hay modelo generado en {path}: corre antes `python -m llm.cycle model ...`")
        parts_import = import_name(path)
    if str(Path.cwd()) not in sys.path:
        sys.path.insert(0, str(Path.cwd()))
    parts = importlib.import_module(parts_import)
    return parts_pack(base, parts, parts_import, spec, f"{problem}_{variant}")


def run_model_stage(problem: str, variant: str, workspace: str | Path, client, rounds: int = 6,
                    model_name: str | None = None) -> dict:
    """Genera las piezas de la variante; si se aceptan, las deja en `<workspace>/model/parts.py`."""
    from .parts_generator import generate_problem_model_parts

    base = base_pack(problem)
    make_spec, _ = base.variants[variant]
    ws = Path(workspace)
    scale = base.make_instances(1, 777, base.parse_size(base.default_size))
    res = generate_problem_model_parts(client, make_spec(), base.load_cases(), ws, max_rounds=rounds, scale_instances=scale,
                                       verbose=False)
    stats = {"problem": problem, "variant": variant, "accepted": res.path is not None,
             "heuristic_rounds": res.heuristic.rounds, "mip_rounds": res.mip.rounds, "llm_calls": res.llm_calls,
             "seconds": round(res.seconds, 1), "tokens": res.tokens.as_dict(model_name),
             "rejections": res.heuristic.reports + res.mip.reports}
    if res.path is not None:
        target = model_path(ws)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(res.path, target)
        stats["model"] = str(target)
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "model_stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    return stats


def _stage_model(args) -> None:
    from .client import OpenAIClient, TranscriptClient

    inner = OpenAIClient(model=args.model or "gpt-5.4-mini")
    client = TranscriptClient(inner, Path(args.workspace) / "transcript")
    stats = run_model_stage(args.problem, args.variant, args.workspace, client, args.rounds, inner.model)
    print(json.dumps({k: v for k, v in stats.items() if k != "rejections"}, indent=2, ensure_ascii=False))
    if not stats["accepted"]:
        raise SystemExit(1)


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    rest: list[str] = []
    if "--" in argv:
        k = argv.index("--")
        argv, rest = argv[:k], argv[k + 1:]
    ap = argparse.ArgumentParser(prog="python -m llm.cycle")
    ap.add_argument("stage", choices=["model", "components", "tune"])
    ap.add_argument("--problem", choices=["clsp", "cvrp"], required=True)
    ap.add_argument("--variant", required=True)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--reference", action="store_true", help="usar las piezas de referencia de la variante")
    ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--model", default=None)
    args = ap.parse_args(argv)
    if args.stage == "model":
        return _stage_model(args)
    pack = load_variant(args.problem, args.variant, args.workspace, args.reference)
    if args.stage == "components":
        from .cli import main as generate

        return generate(pack, ["--from-scratch", "--workspace", args.workspace, "--slots", *CYCLE_SLOTS, *rest])
    from tuning.cli import main as tune

    tune(pack, ["--generated", args.workspace, *rest])


if __name__ == "__main__":
    main()


__all__ = ["CYCLE_SLOTS", "TrivialConstructor", "load_variant", "parts_pack", "parts_problem_spec", "run_model_stage"]
