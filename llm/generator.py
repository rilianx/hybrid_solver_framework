"""Ciclo generar → validar → corregir (§6), como funciones planas.

    generate_slot(client, spec, slot, n_variants, contexts, workspace)
        ├── generation_prompt → client.complete → parse_response → materialize
        ├── validate_generated_module (todas las capas, sobre cada micro-contexto)
        └── por cada rechazado: correction_prompt(feedback) → ... hasta max_rounds

Sin estado escondido: `GenerationStats` acumula lo que §9.3 pide medir
(tasa de aprobación por capa, rondas de corrección por componente) y es
lo que se convertiría en el estado del grafo si algún día esto se
orquesta con LangGraph.
"""

from __future__ import annotations

import dataclasses
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.validation import ValidationContext, ValidationReport, validate_component
from core.validation.base import fail, ok
from core.validation.diversity import improving_neighbors
from core.validation.quality import diversity_check, probe_checks
from core.validation.syntactic import load_module

from .client import LLMClient, TokenUsage
from .parser import ParsedModule, materialize, parse_response
from .prompts import SYSTEM_PROMPT, ProblemSpec, correction_prompt, generation_prompt


@dataclass
class GeneratedComponent:
    name: str
    slot: str
    path: Path
    source: str
    component: dict[str, Any]
    build_component: Any  # callable(problem, **params) -> impl
    rounds: int  # 1 = aceptado a la primera


@dataclass
class GenerationStats:
    slot: str
    requested: int = 0
    parsed: int = 0
    accepted: int = 0
    llm_calls: int = 0
    llm_seconds: float = 0.0
    tokens: TokenUsage = field(default_factory=TokenUsage)  # 0 si el cliente no informa uso
    rejections_by_layer: Counter = field(default_factory=Counter)  # capa -> nº de rechazos (todas las rondas)
    rounds_per_accepted: dict[str, int] = field(default_factory=dict)
    abandoned: list[str] = field(default_factory=list)  # nombres que agotaron max_rounds

    def summary(self) -> str:
        rate = f"{self.accepted}/{self.parsed}" if self.parsed else "0/0"
        layers = ", ".join(f"{k}={v}" for k, v in sorted(self.rejections_by_layer.items())) or "ninguno"
        rounds = ", ".join(f"{k}:{v}" for k, v in self.rounds_per_accepted.items()) or "-"
        return (
            f"slot={self.slot} aceptados={rate} (pedidos {self.requested}) llamadas={self.llm_calls} "
            f"({self.llm_seconds:.0f}s"
            + (f", {self.tokens}" if self.tokens.total_tokens else "")
            + f") rechazos por capa: {layers}; rondas por aceptado: {rounds}"
            + (f"; abandonados: {self.abandoned}" if self.abandoned else "")
        )


def validate_generated_module(
    path: str | Path,
    contexts: list[ValidationContext],
    peers: list[tuple[str, Any]] | None = None,
) -> tuple[ValidationReport, Any, dict | None]:
    """Carga el módulo generado, construye el componente con `build_component(problem)`
    para cada micro-contexto y corre todas las capas. Devuelve el primer reporte
    fallido (o el último exitoso), el módulo y su COMPONENT."""
    path = Path(path)
    report = ValidationReport(subject=f"módulo '{path.name}'")
    module, r = load_module(path)
    report.add(r)
    if module is None:
        return report, None, None
    component = getattr(module, "COMPONENT", None)
    factory = getattr(module, "build_component", None)
    if not isinstance(component, dict):
        report.add(fail("syntactic", "component_present", "el módulo no define el dict COMPONENT"))
    if not callable(factory):
        report.add(fail("syntactic", "factory_present", "el módulo no define `build_component(problem, **params)`"))
    if not report.passed:
        return report, module, component

    # Todas las propiedades deben cumplirse en TODOS los micro-contextos, salvo
    # `neighborhood.improves_from_start`, que basta con que se cumpla en UNO: la
    # solución trivial de algún contexto puede ser un óptimo local para movimientos
    # elementales (nada mejora desde ahí), y exigirlo en todos volvía el gate
    # insatisfacible para operadores legítimos (corrida 4: `single_setup_removal_r1`).
    AGGREGATE_ANY = {"neighborhood.improves_from_start"}
    reports: list[ValidationReport] = []
    for k, ctx0 in enumerate(contexts):
        ctx = dataclasses.replace(ctx0, accepted_peers=list(peers or [])) if peers else ctx0
        try:
            impl = factory(ctx.problem)
        except Exception as exc:  # noqa: BLE001
            report.add(fail("syntactic", "factory_runs", f"build_component(problem) lanzó {type(exc).__name__}: {exc} (micro-instancia {k})"))
            return report, module, component
        reports.append(validate_component(component, impl, ctx))
        hard_fail = [r for r in reports[-1].failures() if r.name not in AGGREGATE_ANY]
        if hard_fail:
            report.extend(reports[-1].results)
            return report, module, component
    report.add(ok("syntactic", "factory_runs"))

    probe = contexts[0].diversity_probe if contexts else None
    slot_name = component.get("slot", "")

    any_fails = [r for rep in reports for r in rep.failures() if r.name in AGGREGATE_ANY]
    if any_fails and len(any_fails) == len(reports):
        # Falló en todos los micro-contextos. Última oportunidad: la sonda grande. Corrida 7:
        # `same_period_setup_swap` no mejoraba desde la partida en 3×5 (18 movimientos, ninguno
        # mejora) pero sí en 10×15 (73 mejoras, todas novedosas); rechazado, el modelo lo
        # "arregló" rellenándolo con flips. La micro-instancia era chica para ese operador.
        rescued = _improves_on_probe(factory, probe, slot_name)
        if rescued is None:
            report.extend(reports[0].results)  # trae el hint con movimientos que sí mejoran
            return report, module, component
        report.add(rescued)

    # Diversidad: sobre la sonda (instancia grande) y con el componente reconstruido allí.
    # Se hace una sola vez, después de las propiedades: rechazar por duplicado a algo que
    # además está mal implementado sería el feedback equivocado.
    if probe is not None:
        try:
            probe_impl = factory(probe.problem)
            report.extend(probe_checks(slot_name, probe_impl, probe))
            if report.passed and peers:
                report.extend(diversity_check(
                    slot_name, probe_impl, peers, probe.solution,
                    probe.problem, probe.max_similarity, probe.min_novelty,
                ))
        except Exception as exc:  # noqa: BLE001 — la sonda no debe tumbar la validación
            report.add(ok("quality", "probe_skipped", f"{type(exc).__name__}: {exc}"))
        if not report.passed:
            return report, module, component

    if reports:
        # aprobado: se reporta el último contexto, sin los fallos agregables que quedaron compensados
        report.extend([r for r in reports[-1].results if r.name not in AGGREGATE_ANY or r.passed])
    return report, module, component


def _improves_on_probe(factory, probe, slot_name: str):
    """OK si el vecindario tiene mejoras desde la partida de la sonda; None si no (o no aplica)."""
    if probe is None or slot_name != "neighborhood":
        return None
    try:
        imp = improving_neighbors(factory(probe.problem), probe.solution, probe.problem)
    except Exception:  # noqa: BLE001
        return None
    if not imp:
        return None
    return ok("quality", "neighborhood.improves_from_start",
              f"sin mejoras desde la partida en las micro-instancias, pero {len(imp)} en la sonda "
              f"({len(probe.solution)}×{len(probe.solution[0])}): las micro-instancias eran chicas para este operador")


def generate_slot(
    client: LLMClient,
    spec: ProblemSpec,
    slot: str,
    n_variants: int,
    contexts: list[ValidationContext],
    workspace: str | Path,
    max_rounds: int = 3,
    avoid_names: list[str] | None = None,
    catalog_peers: list[tuple[str, Any]] | None = None,
    verbose: bool = True,
) -> tuple[list[GeneratedComponent], GenerationStats]:
    """`catalog_peers`: componentes del mismo slot que YA existen (escritos a mano o de
    corridas previas), como (nombre, impl) ligados al ProblemModel del primer contexto.
    El gate de diversidad los usa junto a los aceptados en esta corrida, para que el
    modelo no reinvente un operador que ya está en el catálogo."""
    workspace = Path(workspace)
    stats = GenerationStats(slot=slot, requested=n_variants)
    accepted: list[GeneratedComponent] = []

    def _ask(prompt: str) -> str:
        t0 = time.perf_counter()
        text = client.complete(SYSTEM_PROMPT, prompt)
        stats.llm_calls += 1
        stats.llm_seconds += time.perf_counter() - t0
        used = getattr(client, "last_usage", None)  # los clientes que no cuentan tokens no molestan
        if isinstance(used, TokenUsage):
            stats.tokens.add(used)
        return text

    modules = materialize(parse_response(_ask(generation_prompt(spec, slot, n_variants, avoid_names))), workspace, slot, 1)
    stats.parsed = len(modules)
    if verbose:
        print(f"[{slot}] ronda 1: {len(modules)} módulos parseados")

    pending: list[tuple[ParsedModule, int]] = [(m, 1) for m in modules]
    while pending:
        m, round_no = pending.pop(0)
        # Los pares de comparación se construyen sobre el problema donde se mide la
        # diversidad (la sonda si existe, la micro-instancia si no).
        probe = contexts[0].diversity_probe
        peer_problem = probe.problem if probe is not None else contexts[0].problem
        peers = list(catalog_peers or []) + [
            (c.name, c.build_component(peer_problem)) for c in accepted if c.slot == slot
        ]
        report, module, component = validate_generated_module(m.path, contexts, peers=peers)
        name = (component or {}).get("name", m.name or m.path.stem)
        if report.passed:
            accepted.append(
                GeneratedComponent(
                    name=name, slot=slot, path=m.path, source=m.source, component=component,
                    build_component=module.build_component, rounds=round_no,
                )
            )
            stats.accepted += 1
            stats.rounds_per_accepted[name] = round_no
            if verbose:
                print(f"[{slot}] ✔ {name} aceptado (ronda {round_no})")
            continue

        stats.rejections_by_layer[report.failed_layer or "?"] += 1
        if verbose:
            print(f"[{slot}] ✘ {name} rechazado en '{report.failed_layer}' (ronda {round_no})")
        if round_no >= max_rounds:
            stats.abandoned.append(name)
            continue

        fixed_text = _ask(correction_prompt(spec, slot, m.source, report.feedback()))
        fixed = parse_response(fixed_text)[:1]
        if not fixed:
            stats.abandoned.append(name)
            continue
        fixed[0].name = fixed[0].name or name
        materialize(fixed, workspace, slot, round_no + 1)
        pending.append((fixed[0], round_no + 1))

    if verbose:
        print(stats.summary())
    return accepted, stats


def register_generated(registry, components: list[GeneratedComponent]) -> list[str]:
    """Registra componentes aceptados en un `ComponentRegistry` (impl = build_component).
    Omite nombres ya registrados en el mismo slot y devuelve los nombres agregados."""
    from core.component import ComponentSpec, ComponentSpecError

    added = []
    for c in components:
        try:
            registry.register(ComponentSpec.from_dict(c.component, c.build_component))
            added.append(c.name)
        except ComponentSpecError:
            continue
    return added
