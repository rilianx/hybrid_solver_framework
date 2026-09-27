"""Memoria acotada: lo que queda vivo entre corridas no puede crecer con cada solución evaluada.

Corrida 34 (tuning del gran tour optimizado): el modelo memoizaba el Split con
`lru_cache(maxsize=None)` a nivel de módulo, con el tour como clave. En 5 s no se nota; en horas de
tuning, cada tour distinto quedaba en memoria y los tres runners de GitHub murieron (58 min a 2 h).
Las pruebas de equivalencia y de velocidad no lo ven: miran salidas y tiempo.

La prueba: se evalúan dos tandas de soluciones distintas (la segunda nunca vista) y se mide con
`tracemalloc` cuánta memoria queda retenida después de cada una, con el recolector ya pasado. Una
caché acotada se llena en la primera tanda y no crece en la segunda; una sin límite crece con cada
solución nueva. En los componentes cada tanda usa un componente nuevo sobre un modelo nuevo, así
que una caché del propio componente (vive una corrida) no cuenta, y una de módulo sí; antes de
medir se corren dos tandas para llenar también las cachés acotadas del modelo.
"""

from __future__ import annotations

import gc
import itertools
import tracemalloc
from random import Random
from typing import Callable

from .base import CheckResult, fail, ok

LAYER = "resources"
LIMIT_MB = 1.0
# componentes: lo que retiene la caché acotada del modelo al reemplazar entradas da 0,5-0,9 MB por
# tanda con los vecindarios del gran tour; un dict de módulo por (solución, movimiento), 3-4 MB
COMPONENT_LIMIT_MB = 1.5
BATCH = 10_000
MAX_CACHE = 8192  # lo que se le pide al LLM: cachés con maxsize <= MAX_CACHE (la referencia de gran tour usa 8192)


def _retained_growth(run_batch: Callable[[int], None], warmup: int = 1) -> float:
    """MB retenidos por la última tanda (las anteriores llenan las cachés acotadas)."""
    was = tracemalloc.is_tracing()
    if not was:
        tracemalloc.start()
    try:
        for b in range(warmup):
            run_batch(b)
        gc.collect()
        before = tracemalloc.get_traced_memory()[0]
        run_batch(warmup)
        gc.collect()
        after = tracemalloc.get_traced_memory()[0]
    finally:
        if not was:
            tracemalloc.stop()
    return (after - before) / 1e6


def _verdict(name: str, growth: float, what: str, limit_mb: float) -> CheckResult:
    if growth > limit_mb:
        return fail(LAYER, name, f"{what}: la memoria retenida crece {growth:.1f} MB con {BATCH} soluciones nuevas (límite "
                                 f"{limit_mb:g} MB). Una caché sin límite (lru_cache(maxsize=None), functools.cache, un dict "
                                 f"global que solo crece) agota la memoria en horas de tuning: acótala a maxsize <= {MAX_CACHE} "
                                 f"o guárdala por instancia y no por solución")
    return ok(LAYER, name, f"{what}: {growth:+.2f} MB con {BATCH} soluciones nuevas")


def check_parts_memory(parts, inst, n: int = BATCH, limit_mb: float = LIMIT_MB) -> CheckResult:
    """Las funciones del modelo por piezas se llaman directo: cualquier caché que retengan es de módulo."""

    def run(batch: int) -> None:
        for s in range(n):
            sol = parts.random_solution(inst, Random(1_000_003 * (batch + 1) + s))
            parts.violations(inst, sol)
            parts.cost_terms(inst, sol)

    try:
        growth = _retained_growth(run)
    except Exception as exc:  # noqa: BLE001
        return fail(LAYER, "bounded_memory", f"el modelo lanzó {type(exc).__name__}: {exc} al medir la memoria")
    return _verdict("bounded_memory", growth, "modelo", limit_mb)


def check_component_memory(slot: str, make, problem_factory, inst, sol, n: int = BATCH,
                           limit_mb: float = COMPONENT_LIMIT_MB) -> CheckResult:
    """Cada tanda con un componente y un modelo nuevos: solo cuenta lo que sobrevive a la corrida."""

    def run(batch: int) -> None:
        problem = problem_factory(inst)
        impl = make(problem)
        rng = Random(batch)
        if slot == "neighborhood":
            cur = sol
            for m in itertools.islice(impl.moves(cur), n):
                impl.delta(cur, m)
            for _ in range(60):  # soluciones distintas: aplicar movimientos al azar
                ms = list(itertools.islice(impl.moves(cur), 200))
                if not ms:
                    break
                cur = impl.apply(cur, ms[rng.randrange(len(ms))])
                for m in ms:
                    impl.delta(cur, m)
        elif slot == "perturbation":
            for _ in range(min(n, 2000)):
                impl.perturb(sol, 1.0, rng)
        elif slot == "destruction":
            for _ in range(min(n, 500)):
                impl.destroy(sol, 0.3, rng)
        elif slot == "greedy_score":
            from core.construction import GreedyConstructor

            for k in range(5):
                GreedyConstructor(problem, impl).build(inst, Random(100 * batch + k))
        del impl, problem

    try:
        # dos tandas de calentamiento: también se llenan las cachés acotadas del MODELO, que el
        # componente usa y no son suyas (con una sola, la de 8192 del gran tour aún crecía)
        growth = _retained_growth(run, warmup=2)
    except Exception as exc:  # noqa: BLE001
        return fail(LAYER, "bounded_memory", f"el componente lanzó {type(exc).__name__}: {exc} al medir la memoria")
    return _verdict("bounded_memory", growth, f"componente ({slot})", limit_mb)


__all__ = ["MAX_CACHE", "check_component_memory", "check_parts_memory"]
