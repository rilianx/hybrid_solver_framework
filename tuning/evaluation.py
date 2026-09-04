"""Evaluación en instancias de TEST: lo que el tuner no vio.

El costo de entrenamiento del ganador es optimista por construcción (se eligió
por ser el mínimo entre muchos). La pregunta de §8/§10 —¿el tuning sobre el
catálogo ampliado ayuda o diluye?— solo se responde en instancias nuevas, con
varias semillas, y contra una referencia que no requiera tuning: el default
de cada esqueleto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean, pstdev
from typing import Any

from core.assembler import Assembler, describe


@dataclass
class ConfigScore:
    label: str
    config: dict[str, Any]
    per_instance: list[float]  # costo medio por instancia (sobre semillas)
    per_run: list[float]  # todos los (instancia, semilla)

    @property
    def mean(self) -> float:
        return mean(self.per_run)

    @property
    def std(self) -> float:
        return pstdev(self.per_run) if len(self.per_run) > 1 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {"label": self.label, "summary": describe(self.config), "mean": self.mean, "std": self.std,
                "per_instance": self.per_instance, "config": self.config}


@dataclass
class TestReport:
    tuned: ConfigScore
    baselines: list[ConfigScore] = field(default_factory=list)
    reference: float | None = None  # p.ej. lot-for-lot sin búsqueda

    def best_baseline(self) -> ConfigScore:
        return min(self.baselines, key=lambda s: s.mean)

    def gain_vs_best_baseline(self) -> float:
        b = self.best_baseline().mean
        return (b - self.tuned.mean) / abs(b) if b else 0.0

    def wins_per_instance(self) -> int:
        """En cuántas instancias el afinado gana al mejor default (mismo esqueleto o no)."""
        b = self.best_baseline()
        return sum(1 for x, y in zip(self.tuned.per_instance, b.per_instance) if x < y)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tuned": self.tuned.to_dict(),
            "baselines": [b.to_dict() for b in sorted(self.baselines, key=lambda s: s.mean)],
            "best_baseline": self.best_baseline().label,
            "gain_vs_best_baseline": self.gain_vs_best_baseline(),
            "wins_per_instance": f"{self.wins_per_instance()}/{len(self.tuned.per_instance)}",
            "reference": self.reference,
        }


def score_config(assembler: Assembler, label: str, config: dict[str, Any], instances: list[Any],
                 budget: float, seeds: tuple[int, ...] = (0, 1, 2)) -> ConfigScore:
    per_instance, per_run = [], []
    for inst in instances:
        costs = [assembler.evaluate(config, [inst], budget, seed=s) for s in seeds]
        per_instance.append(mean(costs))
        per_run.extend(costs)
    return ConfigScore(label, config, per_instance, per_run)


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
