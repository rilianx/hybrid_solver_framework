"""Catálogo de componentes de un problema, en la convención del `Assembler`
(`impl(problem, **params)`): los escritos a mano del `ProblemPack` más los generados por LLM
que se aceptaron (`generated/<problema>/<slot>/*.py`, cargados por `load_generated`).

Genérico: no conoce el problema. `examples/<problema>/catalog.py` lo envuelve con su pack.
"""

from __future__ import annotations

from pathlib import Path

from core.component import ComponentRegistry, ComponentSpec
from core.construction import RULES, GreedyConstructor
from core.problem_pack import ProblemPack

from .generator import GeneratedComponent, register_generated, validate_generated_module


def build_registry(pack: ProblemPack, generated: list[GeneratedComponent] | None = None, handwritten: bool = True,
                   exclude_slots: set[str] | None = None) -> ComponentRegistry:
    """`handwritten=False`: solo los generados, salvo en los slots que un esqueleto necesita
    y el LLM no genera (p.ej. `fixing_policy`), donde se mantiene el de mano para que el
    esqueleto exista. Los puntajes (`greedy_score`) no los necesita ningún esqueleto, así
    que los de mano quedan fuera.

    Cada `greedy_score` registrado (a mano o generado) se envuelve además como constructor
    `greedy_<nombre>`: `GreedyConstructor` con ese puntaje, con la regla y α como
    parámetros del tuner (más los parámetros propios del puntaje)."""
    registry = ComponentRegistry()
    generated_slots = {c.slot for c in generated or []}
    for component, factory in pack.handwritten:
        if exclude_slots and component["slot"] in exclude_slots:
            continue
        keep = component["slot"] not in generated_slots and component["slot"] != "greedy_score"
        if handwritten or keep:
            registry.register(ComponentSpec.from_dict(component, factory))
    if generated:
        register_generated(registry, generated)
    for spec in list(registry.for_slot("greedy_score")):
        registry.register(greedy_constructor_spec(spec, pack.constructor_skeletons))
    return registry


def greedy_constructor_spec(score_spec: ComponentSpec, skeletons: list[str]) -> ComponentSpec:
    params = {"rule": {"type": "cat", "values": list(RULES)}, "alpha": {"type": "float", "range": [0.0, 1.0]}}
    params.update(score_spec.params)

    def factory(problem, rule="greedy", alpha=0.2, **score_params):
        return GreedyConstructor(problem, score_spec.make(problem, **score_params), rule=rule, alpha=alpha)

    component = {"name": f"greedy_{score_spec.name}", "slot": "constructor",
                 "compatible_skeletons": list(score_spec.compatible_skeletons) or list(skeletons), "params": params}
    return ComponentSpec.from_dict(component, factory)


def load_generated(pack: ProblemPack, workspace: str | Path | None = None, revalidate: bool = True,
                   verbose: bool = True, combination: bool = True) -> list[GeneratedComponent]:
    """Carga los módulos aceptados de una corrida previa de la generación.

    Con `revalidate=True` vuelve a pasar cada módulo por el validador (sobre
    micro-instancias nuevas), así un módulo que solo pasó por suerte no entra
    al catálogo. Para cada nombre se toma la ronda más alta disponible.
    """
    workspace = Path(workspace or pack.default_workspace)
    if not workspace.exists():
        return []
    # admisión leniente: la utilidad la decide el tuning
    contexts = pack.make_contexts(strict=False, combination=combination) if revalidate else []
    latest: dict[tuple[str, str], Path] = {}
    for path in sorted(workspace.glob("*/*.py")):
        slot = path.parent.name
        if slot in ("model", "problem_model"):  # el ProblemModel del ciclo completo (`llm.cycle`), no un componente
            continue
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
        out.append(GeneratedComponent(component["name"], slot, path, path.read_text(), component, module.build_component,
                                      rounds=int(path.stem.rpartition("_r")[2] or 1)))
    return out


__all__ = ["build_registry", "greedy_constructor_spec", "load_generated"]
