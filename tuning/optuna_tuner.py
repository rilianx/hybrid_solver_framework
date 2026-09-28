"""Tuner con Optuna (TPE, define-by-run) sobre `Assembler.config_space()`.

Por qué Optuna primero y no irace: corre en el mismo proceso Python, sin R, y
el espacio condicional ya se expresa con `suggest_from_space` (§8). irace
queda disponible vía `tuning.irace_scenario` para quien quiera reproducir
con la herramienta estándar del área.

Decisiones:
- Cada *trial* evalúa la configuración en TODAS las instancias de
  entrenamiento con la misma semilla base (costo medio). Es el esquema más
  simple y estable con presupuestos de segundos; racing (irace) sería más
  eficiente pero cambia la comparación.
- Los defaults de cada esqueleto se encolan como primeros trials: el tuner
  no puede quedar por debajo de "elegir el esqueleto por defecto", y si
  queda, es un hallazgo.
- Una configuración que falla devuelve `assembler.penalty_cost`, que Optuna
  ve como un valor muy malo y aprende a evitar.
- Selección final (`reeval_top`): el mínimo de muchos trials evaluados con una sola
  semilla es optimista, y en las runs 13 y 14 el elegido quedó en test hasta 6 puntos
  por encima de su mejor default. Con `reeval_top=k`, el mejor trial de cada una de las k
  mejores elecciones de componentes distintas y el mejor default se re-evalúan en train con `reeval_seeds` semillas más y se elige por la media.
  Cada elección de componentes entre esos k entra además con los parámetros numéricos por
  defecto ("gemelo"): en las runs 19 y 22 el tuner eligió los componentes correctos, pero sus
  numéricos afinados en 5 instancias quedaron en test 0.7 y 2.3 puntos peor que los defaults
  de esa misma elección. Y si el afinado le gana a su gemelo en train por menos que el ruido
  (`prefer_defaults`), se elige el gemelo.
- Carrera en la selección final (`race_seeds`): después de esas semillas, los candidatos que
  pierden contra el líder por más que el ruido (diferencia pareada por instancia y semilla) salen,
  y los que siguen empatados reciben una semilla más, hasta `race_seeds` o hasta que quede uno. En
  la run 35 dos de tres réplicas eligieron SA, que en test quedaba 0,8–1,2 puntos detrás del VNS
  de la tercera. Es el racing de irace, solo en la selección final.
- Sondeo inicial (`screen`): después de los defaults se encolan variantes de un solo componente
  (cada constructor, vecindario… alternativo con lo demás en su default), repartidas entre
  esqueletos y slots. En la run 23 dos de tres réplicas no llegaron a probar bien el constructor
  que, con todo lo demás por defecto, era el mejor en test (4,3 % contra 10-11 %): TPE se había
  quedado en otro constructor desde los primeros trials.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from config_space import ConfigSpace, suggest_from_space
from core.assembler import Assembler, describe


@dataclass
class Trial:
    number: int
    config: dict[str, Any]
    cost: float
    seconds: float
    enqueued: bool = False  # default de un esqueleto, no muestreado
    defaults_of: int | None = None  # gemelo de la selección final: los componentes de ese trial, numéricos por defecto
    per_instance: list[float] | None = None  # costo (normalizado) por instancia con la semilla base

    @property
    def summary(self) -> str:
        return describe(self.config)


@dataclass
class TuningResult:
    best_config: dict[str, Any]
    best_cost: float
    trials: list[Trial] = field(default_factory=list)
    seconds: float = 0.0
    penalty_cost: float = 1e12
    # selección final: [{"number", "summary", "costs", "mean"}] de los re-evaluados (vacío si no hubo)
    reevaluated: list[dict[str, Any]] = field(default_factory=list)
    best_trial_number: int | None = None
    best_is_twin: bool = False  # el elegido es el gemelo con numéricos por defecto de best_trial_number

    @property
    def n_failed(self) -> int:
        return sum(1 for t in self.trials if t.cost >= self.penalty_cost)

    def incumbent_curve(self) -> list[float]:
        """Mejor costo visto hasta cada trial (para graficar convergencia)."""
        curve, best = [], float("inf")
        for t in self.trials:
            best = min(best, t.cost)
            curve.append(best)
        return curve

    def best_default(self) -> Trial | None:
        defaults = [t for t in self.trials if t.enqueued]
        return min(defaults, key=lambda t: t.cost) if defaults else None

    def skeleton_usage(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for t in self.trials:
            out[t.config.get("skeleton", "?")] = out.get(t.config.get("skeleton", "?"), 0) + 1
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    def to_dict(self) -> dict[str, Any]:
        bd = self.best_default()
        return {
            "best_config": self.best_config,
            "best_cost": self.best_cost,
            "best_summary": describe(self.best_config),
            "best_default_cost": bd.cost if bd else None,
            "best_default_summary": bd.summary if bd else None,
            "n_trials": len(self.trials),
            "n_failed": self.n_failed,
            "seconds": round(self.seconds, 1),
            "skeleton_usage": self.skeleton_usage(),
            "best_trial_number": self.best_trial_number,
            "reevaluated": self.reevaluated,
            "best_is_twin": self.best_is_twin,
            "incumbent_curve": self.incumbent_curve(),
            "trials": [
                {"number": t.number, "cost": t.cost, "seconds": round(t.seconds, 2), "enqueued": t.enqueued,
                 "summary": t.summary, "config": t.config}
                for t in self.trials
            ],
        }


def _enqueueable(config: dict[str, Any], space: ConfigSpace) -> dict[str, Any]:
    """Solo los parámetros que existen en el espacio (Optuna rechaza nombres desconocidos)."""
    names = {n.name for n in space.nodes}
    return {k: v for k, v in config.items() if k in names}


def tune_with_optuna(
    assembler: Assembler,
    train_instances: list[Any],
    budget: float,
    n_trials: int,
    seed: int = 0,
    space: ConfigSpace | None = None,
    enqueue_defaults: bool = True,
    timeout: float | None = None,
    on_trial: Callable[[Trial], None] | None = None,
    normalizers: list[float] | None = None,
    reeval_top: int = 0,
    reeval_seeds: int = 2,
    screen: int = 0,
    defaults_margin: float = 0.005,
    race_seeds: int | None = None,
) -> TuningResult:
    """Corre `n_trials` evaluaciones (incluidos los defaults encolados) y devuelve el resultado.

    Con `normalizers` el costo de cada trial es la media de `costo / referencia` por
    instancia (ver `Assembler.evaluate`). Con `reeval_top > 0`, selección final por
    re-evaluación (ver el docstring del módulo); `best_cost` es entonces la media re-evaluada."""
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    space = space or assembler.config_space()
    sampler = optuna.samplers.TPESampler(seed=seed, n_startup_trials=max(5, n_trials // 5))
    study = optuna.create_study(direction="minimize", sampler=sampler)

    enqueued: set[int] = set()
    if enqueue_defaults:
        for k, sk in enumerate(assembler.available_skeletons()):
            study.enqueue_trial(_enqueueable(assembler.default_config(sk), space))
            enqueued.add(k)
    for config in screening_configs(assembler)[:max(0, screen)]:
        study.enqueue_trial(_enqueueable(config, space))

    trials: list[Trial] = []

    def objective(trial: "optuna.Trial") -> float:
        config = suggest_from_space(space, trial)
        t0 = time.perf_counter()
        cost, blocks = evaluate_blocks(assembler, config, train_instances, budget, seed, normalizers)
        rec = Trial(trial.number, config, cost, time.perf_counter() - t0, enqueued=trial.number in enqueued,
                    per_instance=blocks)
        trials.append(rec)
        if on_trial is not None:
            on_trial(rec)
        return cost

    t0 = time.perf_counter()
    study.optimize(objective, n_trials=n_trials, timeout=timeout)
    best = min(trials, key=lambda t: t.cost)
    best_cost, reevaluated = best.cost, []
    if reeval_top > 0:
        best, best_cost, reevaluated = _reevaluate(assembler, trials, train_instances, budget, seed,
                                                   reeval_top, reeval_seeds, normalizers, defaults_margin,
                                                   race_seeds=race_seeds)
    return TuningResult(
        best_config=best.config, best_cost=best_cost, trials=trials,
        seconds=time.perf_counter() - t0, penalty_cost=assembler.penalty_cost,
        reevaluated=reevaluated, best_trial_number=best.defaults_of if best.defaults_of is not None else best.number,
        best_is_twin=best.defaults_of is not None,
    )


def prefer_defaults(tuned: list[float], defaults: list[float], margin: float = 0.005) -> bool:
    """¿Quedarse con los numéricos por defecto? Sí, salvo que el afinado gane en train por más que el
    ruido: más que `margin` (relativo) y más que dos errores estándar de la diferencia pareada por
    semilla. Runs 23-26: en ninguna de 12 réplicas los numéricos afinados ganaron en test a los
    defaults de los mismos componentes; en la run 26 ganaron en train por 0.0008 y perdieron 1.3
    puntos en test."""
    diffs = [d - t for t, d in zip(tuned, defaults)]
    gain = sum(diffs) / len(diffs)
    base = abs(sum(defaults) / len(defaults)) or 1.0
    if len(diffs) > 1:
        m = gain
        se = (sum((x - m) ** 2 for x in diffs) / (len(diffs) - 1) / len(diffs)) ** 0.5
    else:
        se = 0.0
    return gain <= max(margin * base, 2 * se)


def screening_configs(assembler: Assembler) -> list[dict[str, Any]]:
    """Variantes de un solo componente de los defaults, intercaladas: un esqueleto por vez y, dentro
    de cada uno, un slot por vez, para que un sondeo corto cubra todos los slots y esqueletos."""
    per_sk = []
    for sk in assembler.available_skeletons():
        base = assembler.default_config(sk)
        sdef = assembler.skeletons[sk]
        by_slot = [[assembler.default_config(sk, {slot: spec.name}) for spec in assembler.registry.compatible(slot, sk)
                    if spec.name != base[slot]]
                   for slot in sdef.slots + tuple(s for s in sdef.optional_slots if assembler.registry.compatible(s, sk))]
        per_sk.append(_interleave(by_slot))
    return _interleave(per_sk)


def _interleave(lists: list[list]) -> list:
    out, k = [], 0
    while any(k < len(li) for li in lists):
        out += [li[k] for li in lists if k < len(li)]
        k += 1
    return out


SLOT_KEYS = ("constructor", "neighborhood", "perturbation", "destruction", "repair_mip", "fixing_policy")


def defaults_twin(assembler: Assembler, t: Trial) -> Trial | None:
    """Los componentes que eligió el trial, con los parámetros numéricos por defecto."""
    choices = {k: v for k, v in t.config.items() if k in SLOT_KEYS}
    try:
        config = assembler.default_config(t.config["skeleton"], choices)
    except (KeyError, ValueError):
        return None
    return Trial(t.number, config, float("nan"), 0.0, defaults_of=t.number)


def evaluate_blocks(assembler: Assembler, config: dict[str, Any], instances: list[Any], budget: float, seed: int,
                    normalizers: list[float] | None = None) -> tuple[float, list[float]]:
    """Costo por instancia (el mismo que `Assembler.evaluate` sobre la lista: la instancia k con la
    semilla `seed + k`) y su media; si alguna falla o es infactible, el costo es `penalty_cost`."""
    blocks = [assembler.evaluate(config, [inst], budget, seed=seed + k,
                                 normalizers=[normalizers[k]] if normalizers is not None else None)
              for k, inst in enumerate(instances)]
    cost = assembler.penalty_cost if any(b >= assembler.penalty_cost for b in blocks) else sum(blocks) / len(blocks)
    return cost, blocks


def clearly_worse(worse: list[float], leader: list[float]) -> bool:
    """¿`worse` pierde contra `leader` por más que el ruido? Diferencia pareada por bloque (instancia y
    semilla): media mayor que dos errores estándar."""
    diffs = [w - b for w, b in zip(worse, leader)]
    n = len(diffs)
    if n < 2:
        return False
    m = sum(diffs) / n
    se = (sum((d - m) ** 2 for d in diffs) / (n - 1) / n) ** 0.5
    return m > 2 * se and m > 0


def _reevaluate(assembler: Assembler, trials: list[Trial], instances: list[Any], budget: float, seed: int,
                top: int, n_seeds: int, normalizers: list[float] | None,
                defaults_margin: float = 0.005, race_seeds: int | None = None) -> tuple[Trial, float, list[dict[str, Any]]]:
    """El mejor trial de cada una de las `top` mejores elecciones de componentes distintas (más su
    gemelo con numéricos por defecto y el mejor default), con `n_seeds` semillas más.

    Por elección y no por trial: los mejores trials suelen ser la misma elección con otros
    numéricos (run 22: los 5), y el costo de un trial con una semilla es muy ruidoso (run 25: la
    misma configuración, en las mismas instancias, 0.669 y 0.759 según la semilla), así que la
    elección que gana en test puede quedar 5.ª en train y fuera de los 5 mejores trials.

    Carrera (`race_seeds` > `n_seeds`): después de las `n_seeds` semillas de todos, se descartan los
    que pierden contra el líder por más que el ruido (diferencia pareada por instancia y semilla) y
    los que quedan reciben una semilla más, hasta `race_seeds` semillas extra o hasta que quede uno.
    Run 35: con 2 semillas extra, dos de tres réplicas eligieron SA; en test, el VNS de la tercera
    les sacaba 0,8–1,2 puntos. Como en irace, las evaluaciones se gastan donde hay duda."""
    ok = sorted((t for t in trials if t.cost < assembler.penalty_cost), key=lambda t: t.cost)
    cands: list[Trial] = []
    seen: set[str] = set()
    choices: set[str] = set()
    for t in ok:
        choice = repr(sorted((k, v) for k, v in t.config.items() if k == "skeleton" or k in SLOT_KEYS))
        if choice in choices:
            continue
        choices.add(choice)
        seen.add(repr(sorted(t.config.items())))
        cands.append(t)
        if len(cands) >= top:
            break
    for t in [c for c in cands if not c.enqueued]:
        twin = defaults_twin(assembler, t)
        if twin is not None and repr(sorted(twin.config.items())) not in seen:
            seen.add(repr(sorted(twin.config.items())))
            cands.append(twin)
    defaults = [t for t in ok if t.enqueued]
    if defaults and repr(sorted(defaults[0].config.items())) not in seen:
        cands.append(defaults[0])
    if not cands:
        best = min(trials, key=lambda t: t.cost)
        return best, best.cost, []

    max_extra = max(n_seeds, race_seeds or n_seeds)
    # por candidato: costo medio por semilla y bloques (instancia, semilla) en el mismo orden para todos
    costs: list[list[float]] = [[] for _ in cands]
    blocks: list[list[float]] = [[] for _ in cands]
    for i, t in enumerate(cands):
        if t.defaults_of is None and t.per_instance is not None:  # la semilla base ya se conoce
            costs[i].append(t.cost)
            blocks[i] += t.per_instance
        else:
            c, b = evaluate_blocks(assembler, t.config, instances, budget, seed, normalizers)
            costs[i].append(c)
            blocks[i] += b
    alive = list(range(len(cands)))
    eliminated: dict[int, int] = {}
    for j in range(1, max_extra + 1):
        for i in alive:
            c, b = evaluate_blocks(assembler, cands[i].config, instances, budget, seed + 1000 * j, normalizers)
            costs[i].append(c)
            blocks[i] += b
        if j < n_seeds:
            continue
        leader = min(alive, key=lambda i: sum(costs[i]) / len(costs[i]))
        for i in list(alive):
            if i != leader and clearly_worse(blocks[i], blocks[leader]):
                alive.remove(i)
                eliminated[i] = j
        if len(alive) == 1:
            break
    rows = [{"number": t.number, "enqueued": t.enqueued, "twin": t.defaults_of is not None, "summary": t.summary,
             "costs": costs[i], "mean": sum(costs[i]) / len(costs[i]), "seeds": len(costs[i]),
             **({"eliminated_after": eliminated[i]} if i in eliminated else {})}
            for i, t in enumerate(cands)]
    pick = min(alive, key=lambda i: rows[i]["mean"])
    if not cands[pick].enqueued and cands[pick].defaults_of is None:
        twin = next((i for i, c in enumerate(cands) if c.defaults_of == cands[pick].number), None)
        if twin is not None:
            k = min(len(costs[pick]), len(costs[twin]))  # semillas en común
            if prefer_defaults(costs[pick][:k], costs[twin][:k], defaults_margin):
                pick = twin
                rows[twin]["preferred_defaults"] = True
    return cands[pick], rows[pick]["mean"], rows