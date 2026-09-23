"""Evaluación en instancias de TEST: lo que el tuner no vio.

El costo de entrenamiento del ganador es optimista por construcción (se eligió
por ser el mínimo entre muchos). La pregunta de §8/§10 —¿el tuning sobre el
catálogo ampliado ayuda o diluye?— solo se responde en instancias nuevas, con
varias semillas, y contra una referencia que no requiera tuning: el default
de cada esqueleto.

El costo medio en bruto lo domina la instancia de mayor escala. Por eso cada
configuración se resume también como **gap relativo por instancia** contra la mejor
solución conocida de esa instancia (`best_known_costs`: el mínimo entre todas las
corridas evaluadas y, si se da, una referencia externa como el MIP completo), y se
promedian los gaps: cada instancia pesa lo mismo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean, pstdev
from typing import Any, Iterable

from core.assembler import Assembler, describe


@dataclass
class ConfigScore:
    label: str
    config: dict[str, Any]
    per_instance: list[float]  # costo medio por instancia (sobre semillas)
    per_run: list[float]  # todos los (instancia, semilla)
    per_instance_runs: list[list[float]] = field(default_factory=list)  # [instancia][semilla]

    @property
    def mean(self) -> float:
        return mean(self.per_run)

    @property
    def std(self) -> float:
        return pstdev(self.per_run) if len(self.per_run) > 1 else 0.0

    def gaps(self, best_known: list[float]) -> list[float]:
        """Gap relativo por instancia: (costo medio − mejor conocido) / mejor conocido."""
        return [(c - b) / abs(b) if b else 0.0 for c, b in zip(self.per_instance, best_known)]

    def mean_gap(self, best_known: list[float]) -> float:
        return mean(self.gaps(best_known))

    def n_failed(self, penalty_cost: float) -> int:
        return sum(1 for c in self.per_run if c >= penalty_cost)

    def to_dict(self, best_known: list[float] | None = None) -> dict[str, Any]:
        d = {"label": self.label, "summary": describe(self.config), "mean": self.mean, "std": self.std,
             "per_instance": self.per_instance, "config": self.config}
        if best_known is not None:
            d["gap_per_instance"] = self.gaps(best_known)
            d["mean_gap"] = self.mean_gap(best_known)
        return d


@dataclass
class TestReport:
    tuned: ConfigScore
    baselines: list[ConfigScore] = field(default_factory=list)
    reference: float | None = None  # p.ej. lot-for-lot sin búsqueda
    best_known: list[float] | None = None  # mejor costo conocido por instancia (ver best_known_costs)

    def best_baseline(self) -> ConfigScore:
        return min(self.baselines, key=lambda s: s.mean)

    def gain_vs_best_baseline(self) -> float:
        b = self.best_baseline().mean
        return (b - self.tuned.mean) / abs(b) if b else 0.0

    def wins_per_instance(self) -> int:
        """En cuántas instancias el afinado gana al mejor default (mismo esqueleto o no)."""
        b = self.best_baseline()
        return sum(1 for x, y in zip(self.tuned.per_instance, b.per_instance) if x < y)

    def scores(self) -> list[ConfigScore]:
        return [self.tuned, *self.baselines]

    def to_dict(self) -> dict[str, Any]:
        bk = self.best_known
        key = (lambda s: s.mean_gap(bk)) if bk is not None else (lambda s: s.mean)
        d = {
            "tuned": self.tuned.to_dict(bk),
            "baselines": [b.to_dict(bk) for b in sorted(self.baselines, key=key)],
            "best_baseline": self.best_baseline().label,
            "gain_vs_best_baseline": self.gain_vs_best_baseline(),
            "wins_per_instance": f"{self.wins_per_instance()}/{len(self.tuned.per_instance)}",
            "reference": self.reference,
        }
        if bk is not None:
            d["best_known"] = bk
            d["best_baseline_by_gap"] = min(self.baselines, key=key).label
        return d


def best_known_costs(scores: Iterable[ConfigScore], external: list[float | None] | None = None,
                     penalty_cost: float = float("inf")) -> list[float]:
    """Mejor costo visto por instancia entre todas las corridas de `scores` (las fallidas
    no cuentan) y, si se da, una referencia externa por instancia (p.ej. el MIP completo)."""
    scores = list(scores)
    n = len(scores[0].per_instance_runs) if scores else len(external or [])
    best = [float("inf")] * n
    for sc in scores:
        for k, runs in enumerate(sc.per_instance_runs):
            ok = [c for c in runs if c < penalty_cost]
            if ok:
                best[k] = min(best[k], min(ok))
    for k, ref in enumerate(external or []):
        if ref is not None:
            best[k] = min(best[k], ref)
    return best


def score_config(assembler: Assembler, label: str, config: dict[str, Any], instances: list[Any],
                 budget: float, seeds: tuple[int, ...] = (0, 1, 2)) -> ConfigScore:
    per_instance, per_run, runs = [], [], []
    for inst in instances:
        costs = [assembler.evaluate(config, [inst], budget, seed=s) for s in seeds]
        per_instance.append(mean(costs))
        per_run.extend(costs)
        runs.append(costs)
    return ConfigScore(label, config, per_instance, per_run, runs)


def evaluate_on_test(
    assembler: Assembler,
    tuned_config: dict[str, Any],
    test_instances: list[Any],
    budget: float,
    seeds: tuple[int, ...] = (0, 1, 2),
    baselines: dict[str, dict[str, Any]] | None = None,
    reference: float | None = None,
) -> TestReport:
    """`baselines`: {label: config}; por defecto, el default de cada esqueleto disponible."""
    if baselines is None:
        baselines = {f"default:{sk}": assembler.default_config(sk) for sk in assembler.available_skeletons()}
    tuned = score_config(assembler, "tuned", tuned_config, test_instances, budget, seeds)
    scored = [score_config(assembler, label, cfg, test_instances, budget, seeds) for label, cfg in baselines.items()]
    return TestReport(tuned=tuned, baselines=scored, reference=reference)


def one_slot_baselines(assembler: Assembler, skeletons: list[str] | None = None) -> dict[str, dict[str, Any]]:
    """Default de cada esqueleto y, además, una variante por cada componente alternativo de
    cada slot (los demás slots en su default): `SA:neighborhood=merge_consecutive_setups`.

    Con el esqueleto fijo es la comparación en igualdad de condiciones que el tuning sobre
    el espacio completo no da: cada componente generado contra el de mano, con los mismos
    parámetros del esqueleto y el mismo presupuesto.
    """
    out: dict[str, dict[str, Any]] = {}
    for sk in skeletons or assembler.available_skeletons():
        base = assembler.default_config(sk)
        out[f"default:{sk}"] = base
        sdef = assembler.skeletons[sk]
        for slot in sdef.slots + tuple(s for s in sdef.optional_slots if assembler.registry.compatible(s, sk)):
            for spec in assembler.registry.compatible(slot, sk):
                if spec.name != base[slot]:
                    out[f"{sk}:{slot}={spec.name}"] = assembler.default_config(sk, {slot: spec.name})
    return out
