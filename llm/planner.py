"""Generación con planificador: plan → implementar en paralelo → unir → replanificar.

    generate_slot_planned(client, spec, slot, n, contexts, workspace)
        ├── plan            una llamada: N ideas en texto (sin código), distintas entre sí
        ├── implement_one   por idea, en paralelo: implementar → validar → corregir
        │                   (la idea va fija en el prompt de corrección)
        ├── dedupe          en serie: el gate de diversidad entre los aceptados, al final
        └── replan          si faltan, nuevas ideas con las aceptadas y las descartadas a la vista

Frente a `generate_slot` (una llamada con las N variantes, validación en fila):
- la diversidad se decide en la planificación, antes de gastar una implementación, y
  el gate de diversidad pasa a ser la unión final;
- cada implementador recibe UNA idea y el prompt de corrección se la recuerda, para
  que la presión del validador no la degrade hacia lo que pasa (artefacto, §6);
- el tiempo total lo marca la cadena más lenta, no la suma.

Hilos y no procesos: el trabajo pesado de validar es CBC, que PuLP lanza como proceso
aparte, así que los hilos ya reparten la CPU; con procesos habría que serializar
clientes y contextos. Los clientes guardan `last_usage` por hilo (`llm.client`).

Forma de grafo a propósito: `GenerationState` es el estado y `plan`, `implement_one`,
`dedupe` son nodos que leen el estado y devuelven lo que cambian. Migrar a LangGraph
sería envolver cada función como nodo, sin reescribir la lógica.
"""

from __future__ import annotations

import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.validation import ValidationContext
from core.validation.quality import diversity_check

from .client import LLMClient, TokenUsage
from .generator import GeneratedComponent, GenerationStats, validate_generated_module
from .parser import materialize, parse_response
from .prompts import SYSTEM_PROMPT, Idea, ProblemSpec, correction_prompt, generation_prompt, parse_ideas, planning_prompt


@dataclass
class ComponentOutcome:
    """Resultado de implementar una idea (lo que devuelve el nodo `implement_one`)."""

    idea: Idea
    component: GeneratedComponent | None = None
    rounds: int = 0
    llm_calls: int = 0
    llm_seconds: float = 0.0
    tokens: TokenUsage = field(default_factory=TokenUsage)
    rejections_by_layer: Counter = field(default_factory=Counter)
    reason: str = ""  # por qué no se aceptó ("" si se aceptó)


@dataclass
class GenerationState:
    spec: ProblemSpec
    slot: str
    n_target: int
    contexts: list[ValidationContext]
    workspace: Path
    max_rounds: int = 3
    catalog_peers: list[tuple[str, Any]] = field(default_factory=list)
    avoid_names: list[str] = field(default_factory=list)
    ideas: list[Idea] = field(default_factory=list)  # todas las planificadas, en orden
    accepted: list[GeneratedComponent] = field(default_factory=list)  # tras la unión
    accepted_ideas: list[Idea] = field(default_factory=list)
    rejected: list[tuple[Idea, str]] = field(default_factory=list)
    replans: int = 0
    stats: GenerationStats | None = None

    def __post_init__(self) -> None:
        self.workspace = Path(self.workspace)
        if self.stats is None:
            self.stats = GenerationStats(slot=self.slot, requested=self.n_target)


def _ask(client: LLMClient, prompt: str) -> tuple[str, float, TokenUsage | None]:
    t0 = time.perf_counter()
    text = client.complete(SYSTEM_PROMPT, prompt)
    used = getattr(client, "last_usage", None)
    return text, time.perf_counter() - t0, used if isinstance(used, TokenUsage) else None


# ---------------------------------------------------------------------------- nodos
def plan(state: GenerationState, client: LLMClient, n_ideas: int) -> list[Idea]:
    """Pide `n_ideas` ideas nuevas. Descarta nombres ya usados en este slot."""
    text, secs, used = _ask(client, planning_prompt(
        state.spec, state.slot, n_ideas, state.avoid_names or None,
        accepted=state.accepted_ideas or None, rejected=state.rejected or None,
    ))
    state.stats.llm_calls += 1
    state.stats.llm_seconds += secs
    if used is not None:
        state.stats.tokens.add(used)
    taken = {i.name for i in state.ideas} | set(state.avoid_names)
    return [i for i in parse_ideas(text) if i.name not in taken][:n_ideas]


def implement_one(state: GenerationState, client: LLMClient, idea: Idea) -> ComponentOutcome:
    """Implementar → validar → corregir una idea, hasta `max_rounds`. Solo lee el estado
    (corre en paralelo): todo lo que produce vuelve en el `ComponentOutcome`."""
    out = ComponentOutcome(idea)

    def ask(prompt: str) -> str:
        text, secs, used = _ask(client, prompt)
        out.llm_calls += 1
        out.llm_seconds += secs
        if used is not None:
            out.tokens.add(used)
        return text

    prompt = generation_prompt(state.spec, state.slot, 1, state.avoid_names or None, idea=idea)
    for round_no in range(1, state.max_rounds + 1):
        out.rounds = round_no
        modules = parse_response(ask(prompt))[:1]
        if not modules:
            out.reason = f"ronda {round_no}: la respuesta no trajo un bloque ```python```"
            return out
        m = modules[0]
        m.name = idea.name  # archivo por idea: dos ideas nunca se pisan
        materialize([m], state.workspace, state.slot, round_no)
        report, module, component = validate_generated_module(m.path, state.contexts, peers=state.catalog_peers or None)
        if report.passed:
            out.component = GeneratedComponent(
                name=(component or {}).get("name", idea.name), slot=state.slot, path=m.path, source=m.source,
                component=component, build_component=module.build_component, rounds=round_no,
            )
            return out
        out.rejections_by_layer[report.failed_layer or "?"] += 1
        out.reason = f"no pasó la capa '{report.failed_layer}' en {round_no} ronda(s)"
        prompt = correction_prompt(state.spec, state.slot, m.source, report.feedback(), idea=idea)
    return out


def dedupe(state: GenerationState, outcomes: list[ComponentOutcome]) -> tuple[list[ComponentOutcome], list[tuple[ComponentOutcome, str]]]:
    """Unión: recorre los aceptados en el orden de las ideas y descarta los que el gate de
    diversidad considera el mismo operador que uno ya aceptado (de esta ronda o de antes).
    Los componentes del catálogo ya se compararon dentro de cada `implement_one`."""
    probe = state.contexts[0].diversity_probe if state.contexts else None
    names = {c.name for c in state.accepted}
    peers = [(c.name, c.build_component(probe.problem)) for c in state.accepted] if probe is not None else []
    kept, dups = [], []
    for o in outcomes:
        c = o.component
        if c is None:
            continue
        if c.name in names:
            dups.append((o, f"mismo nombre que un componente ya aceptado ({c.name})"))
            continue
        if probe is not None and peers:
            impl = c.build_component(probe.problem)
            failures = [r for r in diversity_check(state.slot, impl, peers, probe.solution, probe.problem,
                                                   probe.max_similarity, probe.min_novelty) if not r.passed]
            if failures:
                dups.append((o, "duplicado de otra idea aceptada: " + failures[0].message[:300]))
                continue
            peers.append((c.name, impl))
        elif probe is not None:
            peers.append((c.name, c.build_component(probe.problem)))
        names.add(c.name)
        kept.append(o)
    return kept, dups


# ---------------------------------------------------------------------------- orquestador
def generate_slot_planned(
    client: LLMClient,
    spec: ProblemSpec,
    slot: str,
    n_variants: int,
    contexts: list[ValidationContext],
    workspace: str | Path,
    max_rounds: int = 3,
    avoid_names: list[str] | None = None,
    catalog_peers: list[tuple[str, Any]] | None = None,
    n_ideas: int | None = None,
    max_workers: int = 4,
    max_replans: int = 1,
    verbose: bool = True,
) -> tuple[list[GeneratedComponent], GenerationStats]:
    """Misma firma y salida que `generate_slot`, con planificador y cadenas en paralelo.
    `n_ideas` (default `n_variants`): ideas pedidas en la primera planificación."""
    t0 = time.perf_counter()
    state = GenerationState(spec, slot, n_variants, contexts, Path(workspace), max_rounds,
                            list(catalog_peers or []), list(avoid_names or []))
    st = state.stats
    ask_for = n_ideas or n_variants
    while True:
        ideas = plan(state, client, ask_for)
        state.ideas += ideas
        st.planned += [i.name for i in ideas]
        if verbose:
            print(f"[{slot}] plan{' (replaneo)' if state.replans else ''}: {[i.name for i in ideas]}")
        if not ideas:
            break
        with ThreadPoolExecutor(max_workers=max(1, min(max_workers, len(ideas)))) as pool:
            outcomes = list(pool.map(lambda i: implement_one(state, client, i), ideas))
        for o in outcomes:
            st.llm_calls += o.llm_calls
            st.llm_seconds += o.llm_seconds
            st.tokens.add(o.tokens)
            st.rejections_by_layer.update(o.rejections_by_layer)
            if o.rounds:
                st.parsed += 1
            if o.component is None:
                st.abandoned.append(o.idea.name)
                state.rejected.append((o.idea, o.reason or "no se logró implementar"))
                if verbose:
                    print(f"[{slot}] ✘ {o.idea.name}: {o.reason}")
        kept, dups = dedupe(state, outcomes)
        for o, why in dups:
            st.duplicates[o.idea.name] = why
            state.rejected.append((o.idea, why))
            if verbose:
                print(f"[{slot}] ≈ {o.idea.name} descartado en la unión: {why[:120]}")
        for o in kept:
            state.accepted.append(o.component)
            state.accepted_ideas.append(o.idea)
            st.accepted += 1
            st.rounds_per_accepted[o.component.name] = o.rounds
            if verbose:
                print(f"[{slot}] ✔ {o.component.name} aceptado (ronda {o.rounds})")
        missing = n_variants - len(state.accepted)
        if missing <= 0 or state.replans >= max_replans:
            break
        state.replans += 1
        ask_for = missing
    st.replans = state.replans
    st.wall_seconds = time.perf_counter() - t0
    if verbose:
        print(st.summary())
    return state.accepted, st


__all__ = ["ComponentOutcome", "GenerationState", "dedupe", "generate_slot_planned", "implement_one", "plan"]
