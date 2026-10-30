"""Catálogo de referencia del job shop (`HANDWRITTEN`), sobre la representación por secuencias.
Registrar, envolver puntajes y cargar generados es genérico (`llm.catalog`)."""

from __future__ import annotations

from core.fixing_policies import SlidingWindowPolicy

from .components import (
    CriticalInsert,
    CriticalKick,
    CriticalSwap,
    EarliestEnd,
    JobOrder,
    MachineRemoval,
    MostWorkRemaining,
    TimeWindowRemoval,
)

CONSTRUCTOR_SKELETONS = ["SA", "ILS", "LNS_MIP", "FIX_OPT", "TS", "VNS", "GRASP", "LOCAL_BRANCH", "MIP_PERTURB"]
LOCAL_SEARCH_SKELETONS = ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"]

HANDWRITTEN = [
    ({"name": "job_order", "slot": "constructor", "compatible_skeletons": CONSTRUCTOR_SKELETONS, "params": {}},
     lambda problem: JobOrder()),
    ({"name": "earliest_end", "slot": "greedy_score", "compatible_skeletons": CONSTRUCTOR_SKELETONS, "params": {}},
     lambda problem: EarliestEnd(problem)),
    ({"name": "most_work_remaining", "slot": "greedy_score", "compatible_skeletons": CONSTRUCTOR_SKELETONS, "params": {}},
     lambda problem: MostWorkRemaining(problem)),
    ({"name": "critical_swap", "slot": "neighborhood", "compatible_skeletons": LOCAL_SEARCH_SKELETONS, "params": {}},
     lambda problem: CriticalSwap(problem)),
    ({"name": "critical_insert", "slot": "neighborhood", "compatible_skeletons": LOCAL_SEARCH_SKELETONS, "params": {}},
     lambda problem: CriticalInsert(problem)),
    ({"name": "critical_kick", "slot": "perturbation", "compatible_skeletons": ["ILS"], "params": {}},
     lambda problem: CriticalKick(problem)),
    ({"name": "time_window_removal", "slot": "destruction", "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"], "params": {}},
     lambda problem: TimeWindowRemoval(problem)),
    ({"name": "machine_removal", "slot": "destruction", "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"], "params": {}},
     lambda problem: MachineRemoval(problem)),
    ({"name": "sliding_window", "slot": "fixing_policy", "compatible_skeletons": ["FIX_OPT"],
      "params": {"window_size": {"type": "int", "range": [1, 4]}, "overlap": {"type": "int", "range": [0, 2]}}},
     lambda problem, window_size=2, overlap=1: SlidingWindowPolicy(window_size, min(overlap, window_size - 1))),
]
