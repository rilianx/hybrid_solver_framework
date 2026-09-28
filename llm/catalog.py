"""Catálogo de componentes de un problema, en la convención del `Assembler`
(`impl(problem, **params)`): los escritos a mano del `ProblemPack` más los generados por LLM
que se aceptaron (`generated/<problema>/<slot>/*.py`, cargados por `load_generated`).

Genérico: no conoce el problema. `examples/<problema>/catalog.py` lo envuelve con su pack.
"""

from __future__ import annotations

from pathlib import Path

from core.component import ComponentRegistry, ComponentSpec
from core.beam_search import BeamSearchConstructor
from core.construction import RULES, GreedyConstructor
from core.phases import PhasedPolicy
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
    parámetros del tuner (más los parámetros propios del puntaje). Si el pack lo pide
    (`beam_constructors`), también como `beam_<nombre>`: beam search con rollout greedy."""
    registry = ComponentRegistry()
    generated_slots = {c.slot for c in generated or []}
    for component, factory in pack.handwritten:
        if exclude_slots and component["slot"] in exclude_slots:
            continue
        keep = component["slot"] not in generated_slots and component["slot"] not in ("greedy_score", "construction_policy", "phase")
        if handwritten or keep:
            registry.register(ComponentSpec.from_dict(component, factory))
    if generated:
        register_generated(registry, generated)
    for spec in list(registry.for_slot("greedy_score")) + list(registry.for_slot("construction_policy")):
        registry.register(greedy_constructor_spec(spec, pack.constructor_skeletons))
        if pack.beam_constructors:
            registry.register(beam_constructor_spec(spec, pack.constructor_skeletons))
    phases = list(registry.for_slot("phase"))
    if phases:
        registry.register(phased_constructor_spec(phases, pack.constructor_skeletons))
        if pack.beam_constructors:
            registry.register(phased_constructor_spec(phases, pack.constructor_skeletons, beam=True))
    return registry


def _union(declared, skeletons) -> list[str]:
    """Esqueletos de un constructor armado con un puntaje: los que declaró el puntaje más los
    del pack (un puntaje generado declara la lista genérica, que no trae los del pack)."""
    return list(dict.fromkeys([*declared, *skeletons])) if declared else list(skeletons)


def greedy_constructor_spec(score_spec: ComponentSpec, skeletons: list[str]) -> ComponentSpec:
    params = {"rule": {"type": "cat", "values": list(RULES)}, "alpha": {"type": "float", "range": [0.0, 1.0]}}
    params.update(score_spec.params)

    def factory(problem, rule="greedy", alpha=0.2, **score_params):
        return GreedyConstructor(problem, score_spec.make(problem, **score_params), rule=rule, alpha=alpha)

    component = {"name": f"greedy_{score_spec.name}", "slot": "constructor",
                 "compatible_skeletons": _union(score_spec.compatible_skeletons, skeletons), "params": params}
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


def beam_constructor_spec(score_spec: ComponentSpec, skeletons: list[str]) -> ComponentSpec:
    """`beam_<puntaje>`: `BeamSearchConstructor` que ordena y poda los hijos con el puntaje
    (`branching`) y los evalúa con un rollout greedy del mismo puntaje. `beam_width=1` es
    el *pilot method*."""
    params = {"beam_width": {"type": "int", "range": [1, 32], "log": True, "default": 4},
              "branching": {"type": "int", "range": [1, 16], "log": True, "default": 4}}
    params.update(score_spec.params)

    def factory(problem, beam_width=4, branching=4, **score_params):
        score = score_spec.make(problem, **score_params)
        return BeamSearchConstructor(problem, score, beam_width=beam_width, branching=branching)

    component = {"name": f"beam_{score_spec.name}", "slot": "constructor",
                 "compatible_skeletons": _union(score_spec.compatible_skeletons, skeletons), "params": params}
    return ComponentSpec.from_dict(component, factory)


MAX_PHASES = 4


def phased_params(phases: list[ComponentSpec], max_phases: int = MAX_PHASES) -> dict:
    """Parámetros de una construcción por fases con cantidad VARIABLE de fases: `n_phases` ∈ [1, K]
    y `phase_1` … `phase_K` (categóricos sobre las fases registradas), cada uno activo solo si
    n_phases ≥ j; los parámetros propios de la fase elegida en la posición j van como
    `p<j>.<fase>.<parámetro>`. Por defecto, todas las fases en el orden del registro (con las de
    FRG a mano, FRG). K = min(`max_phases`, fases registradas): repetir una fase no agrega nada."""
    names = [s.name for s in phases]
    K = max(1, min(max_phases, len(names)))
    params: dict = {"n_phases": {"type": "int", "range": [1, K], "default": K}}
    for j in range(1, K + 1):
        active = {"n_phases": list(range(j, K + 1))} if j > 1 else {}
        spec = {"type": "cat", "values": names, "default": names[j - 1]}
        params[f"phase_{j}"] = dict(spec, when=active) if active else spec
        for ph in phases:
            for p, ps in ph.params.items():
                params[f"p{j}.{ph.name}.{p}"] = dict(ps, when={**active, f"phase_{j}": [ph.name]})
    return params


def make_phased(problem, phases: list[ComponentSpec], kw: dict) -> PhasedPolicy:
    """La `PhasedPolicy` de una configuración de `phased_params`."""
    by_name = {s.name: s for s in phases}
    names = [s.name for s in phases]
    n = int(kw.get("n_phases", len(names)))
    chosen, built = [], []
    for j in range(1, n + 1):
        name = kw.get(f"phase_{j}", names[min(j, len(names)) - 1])
        spec = by_name[name]
        own = {p: kw[f"p{j}.{name}.{p}"] for p in spec.params if f"p{j}.{name}.{p}" in kw}
        chosen.append(name)
        built.append(spec.make(problem, **own))
    return PhasedPolicy(built, names=chosen)


def phased_constructor_spec(phases: list[ComponentSpec], skeletons: list[str], beam: bool = False,
                            max_phases: int = MAX_PHASES) -> ComponentSpec:
    """`greedy_phased` / `beam_phased`: el greedy (con regla y α) o la beam search sobre la política
    por fases que elija el tuner, con cantidad de fases variable (`phased_params`)."""
    params = phased_params(phases, max_phases)
    if beam:
        params.update({"beam_width": {"type": "int", "range": [1, 32], "log": True, "default": 4},
                       "branching": {"type": "int", "range": [1, 16], "log": True, "default": 4}})

        def factory(problem, beam_width=4, branching=4, **kw):
            return BeamSearchConstructor(problem, make_phased(problem, phases, kw), beam_width=beam_width, branching=branching)
    else:
        params.update({"rule": {"type": "cat", "values": list(RULES)}, "alpha": {"type": "float", "range": [0.0, 1.0]}})

        def factory(problem, rule="greedy", alpha=0.2, **kw):
            return GreedyConstructor(problem, make_phased(problem, phases, kw), rule=rule, alpha=alpha)

    declared = [s for ph in phases for s in ph.compatible_skeletons]
    component = {"name": "beam_phased" if beam else "greedy_phased", "slot": "constructor",
                 "compatible_skeletons": _union(list(dict.fromkeys(declared)), skeletons), "params": params}
    return ComponentSpec.from_dict(component, factory)


__all__ = ["build_registry", "greedy_constructor_spec", "beam_constructor_spec", "phased_constructor_spec", "load_generated"]
