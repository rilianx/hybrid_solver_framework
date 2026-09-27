"""Memoria acotada (`core.validation.resources`): corrida 34, un `lru_cache(maxsize=None)` de módulo en
el modelo optimizado del gran tour agotó la memoria de los runners en horas de tuning."""

from __future__ import annotations

import functools
import types
from random import Random

from core.validation.resources import check_component_memory, check_parts_memory
from examples.cvrp import model_parts
from examples.cvrp.components import RelocateNeighborhood


def _with_cache(maxsize):
    cached = functools.lru_cache(maxsize=maxsize)(lambda inst, sol: model_parts.cost_terms(inst, sol))
    mod = types.SimpleNamespace(**{k: getattr(model_parts, k) for k in dir(model_parts) if not k.startswith("_")})
    mod.cost_terms = cached
    return mod


def _inst():
    from examples.cvrp.pack import PACK

    return PACK.make_instances(1, 4242, PACK.parse_size("30"))[0]


def test_an_unbounded_model_cache_is_rejected_and_a_bounded_one_is_not():
    inst = _inst()
    assert check_parts_memory(model_parts, inst, n=3000).passed
    assert check_parts_memory(_with_cache(1024), inst, n=3000).passed
    r = check_parts_memory(_with_cache(None), inst, n=3000)
    assert not r.passed and "maxsize" in r.message


_SEEN: dict = {}


class LeakyRelocate(RelocateNeighborhood):
    def delta(self, sol, m):
        key = (sol, m)
        if key not in _SEEN:
            _SEEN[key] = super().delta(sol, m)
        return _SEEN[key]


class PerRunCache(RelocateNeighborhood):
    def __init__(self, problem):
        super().__init__(problem)
        self._seen = {}  # vive lo que vive el componente: una corrida

    def delta(self, sol, m):
        key = (sol, m)
        if key not in self._seen:
            self._seen[key] = super().delta(sol, m)
        return self._seen[key]


def test_a_module_level_component_cache_is_rejected_and_a_per_run_one_is_not():
    from examples.cvrp.pack import PACK

    inst = _inst()
    sol = PACK.baseline_constructor().build(inst, Random(0))
    assert check_component_memory("neighborhood", PerRunCache, PACK.problem_factory, inst, sol).passed
    r = check_component_memory("neighborhood", LeakyRelocate, PACK.problem_factory, inst, sol)
    assert not r.passed and "bounded_memory" == r.name
