"""Etapa `improve`: mejorar un componente a partir de una base, con diagnósticos.

    base (generada, o una semilla escrita a mano con `--seed`)
      → diagnósticos en instancias de entrenamiento (objetivo, cota inferior, dónde se pierde)
      → el LLM propone UNA variante (módulo completo, nombre nuevo)
      → validación (las mismas capas que la generación)
      → se acepta si gana a la base en instancias APARTADAS (media menor y más victorias que derrotas)
      → la aceptada pasa a ser la base; se itera

Es búsqueda local sobre programas, con el LLM de operador: no reemplaza la generación desde cero
sino que la continúa (desde una máquina o una política generada se puede llegar a algo más fino:
cambiar la regla de un estado, una transición, agregar un estado). Una semilla escrita a mano
(p.ej. FRG como máquina en el CPMP) es conocimiento publicado: queda registrado en
`improve_stats.json` (`seed: true`) y las corridas desde cero siguen sin verla.

Cómo se evalúa cada slot (`Harness`):
- `constructor`: su `build`.
- `greedy_score`, `construction_policy`, `construction_machine`: el greedy o la beam search
  (`--mode`) con ese criterio. La traza de los diagnósticos muestra, para una máquina, el estado
  en cada paso.
"""

from __future__ import annotations

import inspect
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from random import Random
from statistics import mean
from typing import Any

from core.validation.base import ValidationReport, fail

from .client import LLMClient, TokenUsage
from .parser import extract_code_blocks
from .prompts import SYSTEM_PROMPT, protocol_source, slot_hint

IMPROVABLE = ("constructor", "greedy_score", "construction_policy", "construction_machine")


@dataclass
class Base:
    name: str
    slot: str
    source: str
    seed: bool = False  # escrita a mano (conocimiento publicado)
    factory: Any = None  # build_component(problem, **params) o la fábrica del catálogo


@dataclass
class ImproveResult:
    base: str
    slot: str
    seed: bool
    rounds: int = 0
    accepted: list[dict] = field(default_factory=list)  # [{name, path, before, after, wins, losses}]
    rejections: list[str] = field(default_factory=list)
    final: str = ""

    def as_dict(self) -> dict:
        return {"base": self.base, "slot": self.slot, "seed": self.seed, "rounds": self.rounds, "accepted": self.accepted,
                "final": self.final, "rejections": self.rejections}


# ---------------------------------------------------------------- evaluación
class Harness:
    """Arma el constructor con el que se juzga un componente del slot y lo corre en instancias."""

    def __init__(self, pack, registry, slot: str, mode: str = "greedy", beam_width: int = 3, max_seconds: float = 60.0):
        if slot not in IMPROVABLE:
            raise ValueError(f"slot {slot!r} no se puede mejorar aquí; opciones: {IMPROVABLE}")
        if mode not in ("greedy", "beam"):
            raise ValueError("mode debe ser greedy o beam")
        self.pack, self.registry, self.slot, self.mode = pack, registry, slot, mode
        self.beam_width, self.max_seconds = beam_width, max_seconds

    def constructor(self, problem, impl, base_name: str = "base"):
        from core.beam_search import BeamSearchConstructor
        from core.construction import GreedyConstructor

        if self.slot == "constructor":
            return impl
        if self.mode == "greedy":
            return GreedyConstructor(problem, impl)  # as_policy corre una máquina con MachinePolicy
        nb = self.beam_width
        return BeamSearchConstructor(problem, impl, beam_width=nb, branching=2 * nb, max_seconds=self.max_seconds)

    def run(self, factory, inst, base_name: str = "base") -> tuple[float, Any, Any]:
        """(objetivo, solución, problema). Una excepción o una solución infactible cuentan como el
        objetivo con penalización del ProblemModel (o infinito si no hay)."""
        P = self.pack.problem_factory(inst)
        try:
            sol = self.constructor(P, factory(P), base_name).build(inst, Random(0))
        except Exception:  # noqa: BLE001
            return float("inf"), None, P
        return float(P.objective(sol)), sol, P

    def scores(self, factory, instances, base_name: str = "base") -> list[float]:
        return [self.run(factory, inst, base_name)[0] for inst in instances]


def _lower_bound(P, inst) -> float | None:
    view = P.construction_view(inst) if callable(getattr(P, "construction_view", None)) else None
    lb = getattr(view, "lower_bound", None)
    if not callable(lb):
        return None
    try:
        return float(lb(view.empty()))
    except Exception:  # noqa: BLE001
        return None


class _OneState:
    """Un puntaje o una política como máquina de un solo estado, para reutilizar `machine_trace`."""

    def __init__(self, policy, name: str):
        self.policy, self.states = policy, (name,)

    def initial(self, partial):
        return self.states[0], self.policy.init(partial)

    def transition(self, partial, state, memory):
        return state, memory

    def score(self, partial, state, memory, action):
        return self.policy.score(partial, memory, action)

    def update(self, partial, state, memory, action):
        return self.policy.update(partial, memory, action)


def _trace(harness: Harness, factory, inst, base_name: str, max_steps: int = 60) -> str:
    """Las acciones del greedy en una instancia, por tramos del mismo estado (una máquina) o de
    corrido (un puntaje o una política)."""
    from core.construction import as_policy, is_machine
    from core.machine import MachinePolicy, compress_trace, machine_trace

    P = harness.pack.problem_factory(inst)
    if harness.slot == "constructor" or not callable(getattr(P, "construction_view", None)):
        return ""
    impl = factory(P)
    machine = impl if is_machine(impl) else _OneState(as_policy(impl), base_name)
    return compress_trace(machine_trace(MachinePolicy(machine), P.construction_view(inst), max_steps=20_000), max_steps)


def diagnostics(harness: Harness, base: Base, factory, instances) -> str:
    rows, worst = [], None
    for k, inst in enumerate(instances):
        obj, _, P = harness.run(factory, inst, base.name)
        lb = _lower_bound(P, inst)
        gap = (obj - lb) / max(1.0, abs(lb)) if lb is not None and obj != float("inf") else None
        rows.append(f"- instancia {k}: objetivo {obj:g}" + (f", cota inferior {lb:g} (brecha {gap:+.0%})" if lb is not None else ""))
        key = gap if gap is not None else obj
        if worst is None or key > worst[0]:
            worst = (key, k, inst)
    out = "\n".join(rows)
    if worst is not None:
        text = repr(worst[2])
        text = text if len(text) <= 600 else text[:600] + "…"
        trace = _trace(harness, factory, worst[2], base.name)
        out += f"\n\nLa peor (instancia {worst[1]}):\n```\n{text}\n```"
        if trace:
            out += f"\nLo que hace la base ahí (greedy, acción por acción; `estado: acciones`):\n```\n{trace}\n```"
    return out


def compare(before: list[float], after: list[float]) -> tuple[bool, str, int, int]:
    wins = sum(a < b for a, b in zip(after, before))
    losses = sum(a > b for a, b in zip(after, before))
    finite = [(b, a) for b, a in zip(before, after) if b != float("inf") and a != float("inf")]
    mb = mean(b for b, _ in finite) if finite else float("inf")
    ma = mean(a for _, a in finite) if finite else float("inf")
    worse_inf = sum(a == float("inf") and b != float("inf") for b, a in zip(before, after))
    ok = worse_inf == 0 and ma < mb and wins > losses
    msg = (f"en {len(before)} instancias apartadas: media {ma:.2f} contra {mb:.2f} de la base, gana en {wins}, pierde en "
           f"{losses}" + (f", falla (excepción o infactible) en {worse_inf} donde la base no" if worse_inf else ""))
    return ok, msg, wins, losses


# ---------------------------------------------------------------- bases
def base_from_workspace(workspace: str | Path, slot: str, name: str) -> Base:
    """La versión más reciente de un componente generado (`<slot>/<name>_r<k>.py`)."""
    from core.validation.syntactic import load_module

    paths = sorted(Path(workspace, slot).glob(f"{name}_r*.py"), key=lambda p: int(p.stem.rpartition("_r")[2] or 0))
    if not paths:
        raise SystemExit(f"no hay {slot}/{name}_r*.py en {workspace}")
    module, r = load_module(paths[-1])
    if module is None:
        raise SystemExit(f"no se pudo cargar {paths[-1]}: {r.message}")
    return Base(name, slot, paths[-1].read_text(), seed=False, factory=module.build_component)


def base_from_handwritten(pack, slot: str, name: str) -> Base:
    """Una semilla escrita a mano: el módulo que define la clase del componente del catálogo."""
    for component, factory in pack.handwritten:
        if component["name"] == name and component["slot"] == slot:
            inst = pack.make_instances(1, 0, pack.parse_size(pack.micro_size or pack.default_size))[0]
            obj = factory(pack.problem_factory(inst))
            module = inspect.getmodule(type(obj))
            # imports relativos → absolutos: la variante vive en el workspace, no en el paquete
            source = re.sub(r"^from \.(\w*) import", lambda m: f"from {module.__package__}{'.' + m.group(1) if m.group(1) else ''} import",
                            inspect.getsource(module), flags=re.M)
            return Base(name, slot, source, seed=True, factory=factory)
    raise SystemExit(f"el pack {pack.name} no tiene un componente a mano {slot}/{name}")


# ---------------------------------------------------------------- prompt
def improve_prompt(spec, base: Base, diag: str, previous: list[str], new_name: str) -> str:
    who = ("Es un componente escrito a mano (una heurística publicada); el módulo de abajo lo define junto con otros: "
           "devuelve un módulo NUEVO con solo tu versión. Puedes importar funciones de los mismos módulos."
           if base.seed else "Lo generó antes este mismo proceso y ya pasó la validación.")
    parts = [
        f"# Tarea\nMejora el componente `{base.name}` (slot `{base.slot}`) del problema **{spec.name}**. {who} "
        "Propón UNA versión que construya mejores soluciones: mira los diagnósticos, en particular dónde la base pierde "
        "respecto de la cota inferior, y cambia la idea donde haga falta (una regla, una condición de entrada o de "
        "término, un desempate, un estado nuevo, una transición), no solo un parámetro: los parámetros los afina el tuner.",
        f"\nUsa `COMPONENT[\"name\"] = \"{new_name}\"` y el mismo slot. La versión se acepta solo si gana a la base en "
        "instancias que no ves (media menor y más victorias que derrotas) y pasa las mismas validaciones que cualquier "
        "componente nuevo.",
        f"\n# Contrato del slot `{base.slot}` (Protocol exacto)\n```python\n{protocol_source(base.slot)}```",
        "\n# Propiedades que verificará el validador\n" + slot_hint(spec, base.slot),
        f"\n# Problema\n{spec.description}",
    ]
    if spec.construction_source:
        parts.append(f"\n## Vista constructiva: el estado parcial y la acción\n```python\n{spec.construction_source}\n```")
    if spec.notes:
        parts.append("\n## Avisos\n" + "\n".join(f"- {n}" for n in spec.notes))
    parts.append(f"\n# Base\n```python\n{base.source}\n```")
    parts.append(f"\n# Diagnósticos de la base (instancias de entrenamiento)\n{diag}")
    if previous:
        parts.append("\n# Intentos anteriores rechazados (no los repitas)\n" + "\n".join(f"- {p}" for p in previous[-4:]))
    parts.append("\nDevuelve UN solo bloque ```python``` con el módulo completo (COMPONENT y build_component(problem, **params)).")
    return "\n".join(parts)


def _new_name(base_name: str, k: int) -> str:
    stem = re.sub(r"_v\d+$", "", base_name)
    return f"{stem}_v{k}"


# ---------------------------------------------------------------- bucle
def improve_component(client: LLMClient, pack, registry, spec, base: Base, workspace: str | Path, harness: Harness,
                      rounds: int = 4, n_train: int = 4, n_test: int = 8, size: str | None = None, seed: int = 9100,
                      tokens: TokenUsage | None = None, deadline: float | None = None,
                      verbose: bool = True) -> ImproveResult:
    from .generator import validate_generated_module

    tokens = tokens if tokens is not None else TokenUsage()
    sz = pack.parse_size(size or pack.default_size)
    train = pack.make_instances(n_train, seed, sz)
    test = pack.make_instances(n_test, seed + 1000, sz)
    contexts = pack.make_contexts(strict=False)
    out_dir = Path(workspace) / base.slot
    out_dir.mkdir(parents=True, exist_ok=True)
    res = ImproveResult(base=base.name, slot=base.slot, seed=base.seed)
    cur, cur_factory = base, base.factory
    cur_scores = harness.scores(cur_factory, test, cur.name)
    version = 1 + max([int(m.group(1)) for p in out_dir.glob("*_v*_r*.py")
                       if (m := re.search(r"_v(\d+)_r", p.name))] + [0])
    previous: list[str] = []
    last = 0.0
    for rnd in range(1, rounds + 1):
        if rnd > 1 and deadline is not None and deadline - time.monotonic() < last:
            res.rejections.append(f"sin tiempo para la ronda {rnd}")
            break
        t0 = time.monotonic()
        res.rounds = rnd
        name = _new_name(cur.name, version)
        text = client.complete(SYSTEM_PROMPT, improve_prompt(spec, cur, diagnostics(harness, cur, cur_factory, train), previous, name))
        used = getattr(client, "last_usage", None)
        if isinstance(used, TokenUsage):
            tokens.add(used)
        blocks = extract_code_blocks(text)
        if not blocks:
            previous.append("la respuesta no traía un bloque ```python```")
            res.rejections.append(previous[-1])
            continue
        path = out_dir / f"{name}_r1.py"
        path.write_text(blocks[0])
        report, module, component = validate_generated_module(path, contexts)
        if report.passed and isinstance(component, dict) and component.get("slot") != base.slot:
            report = ValidationReport(subject=path.name)
            report.add(fail("syntactic", "same_slot", f"el slot debe ser {base.slot}, no {component.get('slot')}"))
        if not report.passed:
            previous.append(f"`{name}`: {report.feedback()[:600]}")
            res.rejections.append(report.feedback())
            path.unlink()
            last = time.monotonic() - t0
            if verbose:
                print(f"[improve/{base.slot}] ✘ ronda {rnd}: {report.failed_layer}")
            continue
        new_name = component.get("name", name)
        new_scores = harness.scores(module.build_component, test, new_name)
        ok, msg, wins, losses = compare(cur_scores, new_scores)
        last = time.monotonic() - t0
        if not ok:
            previous.append(f"`{new_name}` pasó la validación pero no gana a la base: {msg}")
            res.rejections.append(previous[-1])
            path.unlink()
            if verbose:
                print(f"[improve/{base.slot}] ✘ ronda {rnd}: {msg}")
            continue
        res.accepted.append({"name": new_name, "path": str(path), "from": cur.name, "before": round(mean(cur_scores), 3),
                             "after": round(mean(new_scores), 3), "wins": wins, "losses": losses, "round": rnd})
        if verbose:
            print(f"[improve/{base.slot}] ✔ ronda {rnd}: {new_name} — {msg}")
        cur = Base(new_name, base.slot, blocks[0], seed=False, factory=module.build_component)
        cur_factory, cur_scores = module.build_component, new_scores
        version += 1
        previous = []
    res.final = cur.name
    return res


def save_stats(workspace: str | Path, res: ImproveResult, tokens: TokenUsage, model: str = "") -> Path:
    path = Path(workspace) / "improve_stats.json"
    runs = json.loads(path.read_text()) if path.exists() else []
    runs.append({**res.as_dict(), "tokens": tokens.as_dict(model)})
    path.write_text(json.dumps(runs, indent=2, ensure_ascii=False))
    return path


def main(pack, argv: list[str] | None = None, workspace: str | None = None, registry=None, spec=None) -> ImproveResult:
    """CLI genérico: `python -m examples.<problema>.improve --slot construction_machine --base frg_machine --seed`."""
    import argparse

    ap = argparse.ArgumentParser(description="Mejorar un componente desde una base, con diagnósticos (etapa improve)")
    ap.add_argument("--slot", required=True, choices=IMPROVABLE)
    ap.add_argument("--base", required=True, help="nombre del componente base")
    ap.add_argument("--seed", action="store_true", help="la base es un componente escrito a mano del pack (semilla)")
    ap.add_argument("--mode", choices=["greedy", "beam"], default="greedy")
    ap.add_argument("--beam-width", type=int, default=3)
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--train", type=int, default=4)
    ap.add_argument("--test", type=int, default=8)
    ap.add_argument("--size", default=None)
    ap.add_argument("--workspace", default=workspace or pack.default_workspace)
    ap.add_argument("--max-minutes", type=float, default=35.0)
    ap.add_argument("--provider", choices=["openai", "anthropic"], default="openai")
    ap.add_argument("--model", default=None)
    args = ap.parse_args(argv)

    from .catalog import build_registry, load_generated
    from .client import TranscriptClient

    base = base_from_handwritten(pack, args.slot, args.base) if args.seed else base_from_workspace(args.workspace, args.slot, args.base)
    if registry is None:
        registry = build_registry(pack, load_generated(pack, args.workspace, verbose=False), handwritten=True)
    spec = spec or pack.make_spec()
    if args.provider == "anthropic":
        from .client import AnthropicClient as Client
    else:
        from .client import OpenAIClient as Client
    inner = Client(model=args.model) if args.model else Client()
    client = TranscriptClient(inner, Path(args.workspace) / "transcript_improve")
    harness = Harness(pack, registry, args.slot, args.mode, args.beam_width)
    tokens = TokenUsage()
    res = improve_component(client, pack, registry, spec, base, args.workspace, harness, rounds=args.rounds,
                            n_train=args.train, n_test=args.test, size=args.size, tokens=tokens,
                            deadline=time.monotonic() + 60 * args.max_minutes)
    print(json.dumps(res.as_dict(), indent=2, ensure_ascii=False)[:4000])
    save_stats(args.workspace, res, tokens, getattr(inner, "model", ""))
    return res


def _module_main(argv: list[str] | None = None) -> None:
    """`python -m llm.improver --problem cpmp --slot construction_machine --base frg_machine --seed ...`: con el pack
    de referencia del problema (el ciclo sobre un modelo generado usa `python -m llm.cycle improve`)."""
    import sys

    argv = list(sys.argv[1:] if argv is None else argv)
    if "--problem" not in argv:
        raise SystemExit("falta --problem (clsp, cvrp o cpmp)")
    k = argv.index("--problem")
    problem = argv[k + 1]
    del argv[k:k + 2]
    from .cycle import base_pack

    pack = base_pack(problem)
    main(pack, argv, workspace=f"generated/{pack.name}_improve")


__all__ = ["Base", "Harness", "ImproveResult", "improve_component", "base_from_workspace", "base_from_handwritten",
           "diagnostics", "compare", "improve_prompt", "main"]


if __name__ == "__main__":
    _module_main()
