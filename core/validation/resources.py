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

Revisión estática (`static_cache_check`, instantánea): los `lru_cache` del módulo (y de los objetos
que guarda, un nivel adentro) sin límite o con más de `MAX_CACHE` entradas. Corre siempre, también
al aceptar un modelo o un componente. La medición con tracemalloc solo corre si el código es lo
bastante rápido para hacerla en `seconds` (corrida 56: el modelo del CLSP resuelve dos LP por
evaluación, 39 por segundo, y 30 mil evaluaciones por candidato no cabían en el job; ese mismo
modelo, aceptado en la etapa del modelo, tenía un lru_cache(maxsize=None)).
"""

from __future__ import annotations

import gc
import itertools
import sys
import time
import tracemalloc
import types
from random import Random
from typing import Callable

from .base import CheckResult, fail, ok, describe_exception

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


def _lru_wrappers(obj, depth: int = 2, seen: set | None = None):
    """(nombre, función con cache_info) alcanzables desde `obj`: sus atributos o claves, y los de los
    objetos que guardan, hasta `depth` niveles (los módulos importados no se recorren)."""
    seen = set() if seen is None else seen
    if id(obj) in seen or depth < 0:
        return
    seen.add(id(obj))
    if isinstance(obj, dict):
        items = list(obj.items())[:200]
    elif isinstance(obj, (types.ModuleType, types.SimpleNamespace)) or hasattr(obj, "__dict__") or hasattr(obj, "__slots__"):
        names = list(getattr(obj, "__dict__", {}) or {}) + list(getattr(type(obj), "__slots__", ()) or ())
        items = [(n, getattr(obj, n, None)) for n in names]
    else:
        return
    for name, val in items:
        if callable(getattr(val, "cache_info", None)) and hasattr(val, "cache_parameters"):
            yield str(name), val
        elif isinstance(val, types.ModuleType) or isinstance(val, type) or callable(val):
            continue
        elif isinstance(val, (dict, types.SimpleNamespace)) or hasattr(val, "__dict__") or hasattr(val, "__slots__"):
            yield from _lru_wrappers(val, depth - 1, seen)


def static_cache_check(obj, what: str = "módulo") -> CheckResult:
    """lru_cache sin límite o con más de MAX_CACHE entradas en el módulo (o en lo que guarda)."""
    bad = []
    for name, fn in _lru_wrappers(obj):
        size = fn.cache_parameters().get("maxsize")
        if size is None or size > MAX_CACHE:
            bad.append(f"{name} (maxsize={size})")
    if bad:
        return fail(LAYER, "bounded_cache", f"{what}: caché sin límite o demasiado grande en {', '.join(sorted(set(bad)))}. "
                                            f"El tuner evalúa millones de soluciones distintas durante horas: usa "
                                            f"lru_cache(maxsize=<= {MAX_CACHE})")
    return ok(LAYER, "bounded_cache", f"{what}: cachés acotadas")


def _affordable(one: Callable[[], None], calls: int, seconds: float) -> bool:
    """¿Caben `calls` llamadas a `one` en `seconds`? Se mide con unas pocas."""
    t0, k = time.perf_counter(), 0
    while k < 20 and time.perf_counter() - t0 < 0.5:
        one()
        k += 1
    rate = k / max(time.perf_counter() - t0, 1e-9)
    return rate * seconds >= calls


def _verdict(name: str, growth: float, what: str, limit_mb: float, n: int = BATCH) -> CheckResult:
    if growth > limit_mb:
        return fail(LAYER, name, f"{what}: la memoria retenida crece {growth:.1f} MB con {n} soluciones nuevas (límite "
                                 f"{limit_mb:g} MB). Una caché sin límite (lru_cache(maxsize=None), functools.cache, un dict "
                                 f"global que solo crece) agota la memoria en horas de tuning: acótala a maxsize <= {MAX_CACHE} "
                                 f"o guárdala por instancia y no por solución")
    return ok(LAYER, name, f"{what}: {growth:+.2f} MB con {n} soluciones nuevas")


def check_parts_memory(parts, inst, n: int = BATCH, limit_mb: float = LIMIT_MB, seconds: float = 60.0) -> CheckResult:
    """Las funciones del modelo por piezas se llaman directo: cualquier caché que retengan es de módulo.
    Primero la revisión estática; la medición, solo si las 3·n evaluaciones caben en `seconds`."""
    static = static_cache_check(parts, "modelo")
    if not static.passed:
        return static
    probe = iter(range(10**9))

    def one() -> None:
        sol = parts.random_solution(inst, Random(7_000_001 + next(probe)))
        parts.violations(inst, sol)
        parts.cost_terms(inst, sol)

    if not _affordable(one, 2 * n, seconds):
        return ok(LAYER, "bounded_memory", "modelo: cachés acotadas (sin medición dinámica: el modelo es lento)")

    def run(batch: int) -> None:
        for s in range(n):
            sol = parts.random_solution(inst, Random(1_000_003 * (batch + 1) + s))
            parts.violations(inst, sol)
            parts.cost_terms(inst, sol)

    try:
        growth = _retained_growth(run)
    except Exception as exc:  # noqa: BLE001
        return fail(LAYER, "bounded_memory", f"el modelo lanzó {describe_exception(exc)} al medir la memoria")
    return _verdict("bounded_memory", growth, "modelo", limit_mb, n)


def check_component_memory(slot: str, make, problem_factory, inst, sol, n: int = BATCH,
                           limit_mb: float = COMPONENT_LIMIT_MB, seconds: float = 60.0) -> CheckResult:
    """Cada tanda con un componente y un modelo nuevos: solo cuenta lo que sobrevive a la corrida.
    Primero la revisión estática del módulo del componente; la medición, solo si cabe en `seconds`."""
    impl0 = make(problem_factory(inst))
    module = sys.modules.get(type(impl0).__module__)
    static = static_cache_check(module if module is not None else impl0, f"componente ({slot})")
    if not static.passed:
        return static
    if slot == "neighborhood":
        ms = list(itertools.islice(impl0.moves(sol), 50)) or [None]
        it = itertools.cycle(ms)
        one = (lambda: impl0.delta(sol, next(it))) if ms[0] is not None else (lambda: None)
        calls = 3 * (n + 60 * 200)
    else:
        one, calls = (lambda: None), 0
    if calls and not _affordable(one, calls, seconds):
        return ok(LAYER, "bounded_memory", f"componente ({slot}): cachés acotadas (sin medición dinámica: es lento)")

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
        return fail(LAYER, "bounded_memory", f"el componente lanzó {describe_exception(exc)} al medir la memoria")
    return _verdict("bounded_memory", growth, f"componente ({slot})", limit_mb)


__all__ = ["MAX_CACHE", "check_component_memory", "check_parts_memory", "static_cache_check"]
