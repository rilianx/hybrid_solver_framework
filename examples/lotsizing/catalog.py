"""Catálogo de componentes del CLSP en la convención de ensamblaje
(`impl(problem, **params)`), listo para el `Assembler`.

Junta los componentes escritos a mano (`components.py`, las políticas de
fijación del núcleo) con los generados por LLM que hayan sido aceptados
(`generated/clsp/<slot>/*.py`, cargados por `load_generated`).
"""

from __future__ import annotations

from pathlib import Path

from core.component import ComponentRegistry, ComponentSpec
from core.fixing_policies import SlidingWindowPolicy
from llm.generator import GeneratedComponent, register_generated, validate_generated_module

from .components import (
    LotForLotConstructor,
    PeriodWindowDestruction,
    RandomSetupDestruction,
    SetupFlipNeighborhood,
    SetupFlipPerturbation,
)
from .llm_spec import make_contexts

HANDWRITTEN = [
    (
        {"name": "lot_for_lot", "slot": "constructor", "compatible_skeletons": ["SA", "ILS", "LNS_MIP", "FIX_OPT", "TS", "VNS", "GRASP", "LOCAL_BRANCH"], "params": {}},
        lambda problem: LotForLotConstructor(),
    ),
    (
        {"name": "setup_flip", "slot": "neighborhood", "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP"], "params": {}},
        lambda problem: SetupFlipNeighborhood(problem),
    ),
    (
        {"name": "setup_flip_perturbation", "slot": "perturbation", "compatible_skeletons": ["ILS"], "params": {}},
        lambda problem: SetupFlipPerturbation(),
    ),
    (
        {"name": "period_window", "slot": "destruction", "compatible_skeletons": ["LNS_MIP"], "params": {}},
        lambda problem: PeriodWindowDestruction(problem.inst),
    ),
    (
        {"name": "random_setups", "slot": "destruction", "compatible_skeletons": ["LNS_MIP"], "params": {}},
        lambda problem: RandomSetupDestruction(problem.inst),
    ),
    (
        {
            "name": "sliding_window",
            "slot": "fixing_policy",
            "compatible_skeletons": ["FIX_OPT"],
            "params": {"window_size": {"type": "int", "range": [1, 4]}, "overlap": {"type": "int", "range": [0, 2]}},
        },
        lambda problem, window_size=2, overlap=1: SlidingWindowPolicy(window_size, min(overlap, window_size - 1)),
    ),
]


def build_registry(generated: list[GeneratedComponent] | None = None) -> ComponentRegistry:
    registry = ComponentRegistry()
    for component, factory in HANDWRITTEN:
        registry.register(ComponentSpec.from_dict(component, factory))
    if generated:
        register_generated(registry, generated)
    return registry


def load_generated(workspace: str | Path = "generated/clsp", revalidate: bool = True, verbose: bool = True) -> list[GeneratedComponent]:
    """Carga los módulos aceptados de una corrida previa de `generate.py`.

    Con `revalidate=True` vuelve a pasar cada módulo por el validador (sobre
    micro-instancias nuevas), así un módulo que solo pasó por suerte no entra
    al catálogo. Para cada nombre se toma la ronda más alta disponible.
    """
    workspace = Path(workspace)
    if not workspace.exists():
        return []
    contexts = make_contexts() if revalidate else []
    latest: dict[tuple[str, str], Path] = {}
    for path in sorted(workspace.glob("*/*.py")):
        slot = path.parent.name
        base, _, rnd = path.stem.rpartition("_r")
        key = (slot, base)
        if key not in latest or int(rnd or 0) > int(latest[key].stem.rpartition("_r")[2] or 0):
            latest[key] = path

    out: list[GeneratedComponent] = []
    for (slot, base), path in latest.items():
        report, module, component = validate_generated_module(path, contexts) if revalidate else (None, None, None)
        if revalidate and not report.passed:
            if verbose:
                print(f"[catálogo] descartado {path.name}: {report.failed_layer}")
            continue
        if module is None:
            from core.validation.syntactic import load_module

            module, _ = load_module(path)
            component = getattr(module, "COMPONENT", None)
        if module is None or not isinstance(component, dict) or not callable(getattr(module, "build_component", None)):
            continue
        out.append(GeneratedComponent(component["name"], slot, path, path.read_text(), component, module.build_component, rounds=int(path.stem.rpartition("_r")[2] or 1)))
    return out
