"""Catálogo de referencia del job shop (`HANDWRITTEN`), sobre la representación por secuencias.
El registro es genérico (`core.catalog`)."""

from __future__ import annotations


from .components import (
    CriticalInsert,
    CriticalKick,
    CriticalSwap,
    OrderRelink,
    EarliestEnd,
    JobOrder,
    MachineRemoval,
    MostWorkRemaining,
    TimeWindowRemoval,
)

CONSTRUCTOR_SKELETONS = ["SA", "ILS", "TS", "VNS", "PR", "HYB"]
LOCAL_SEARCH_SKELETONS = ["SA", "ILS", "TS", "VNS", "PR", "HYB"]

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
    ({"name": "critical_kick", "slot": "perturbation", "compatible_skeletons": ["ILS", "PR", "HYB"], "params": {}},
     lambda problem: CriticalKick(problem)),
    ({"name": "machine_order", "slot": "relink", "compatible_skeletons": ["PR"], "params": {}},
     lambda problem: OrderRelink(problem)),
    ({"name": "time_window_removal", "slot": "destruction", "compatible_skeletons": ["HYB"], "params": {}},
     lambda problem: TimeWindowRemoval(problem)),
    ({"name": "machine_removal", "slot": "destruction", "compatible_skeletons": ["HYB"], "params": {}},
     lambda problem: MachineRemoval(problem)),
]
