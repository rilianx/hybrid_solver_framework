"""Correr una configuración del tuner entera en C++ (`hsf::solve`, `native/include/hsf/core.hpp`).

El `Assembler` de Python sigue siendo la fuente de la configuración: el espacio, los valores por
defecto de los esqueletos y de los componentes y la lista de vecindarios del shake de VNS salen de
su registro, así una configuración afinada en Python corre igual en C++. Los nombres de los
componentes nativos son los mismos que los del catálogo de Python.

    runner = NativeRunner(assembler, native_module, model_of)
    res = runner.assemble(config)(inst, Random(0), 5.0)    # core.skeleton.RunResult
"""

from __future__ import annotations

from random import Random
from typing import Any, Callable

from core.skeleton import RunResult

NATIVE_SKELETONS = ("SA", "ILS", "VNS", "TS")


class NativeRunner:
    def __init__(self, assembler, native, model_of: Callable[[Any], Any]):
        self.assembler, self.native, self.model_of = assembler, native, model_of

    def full_config(self, config: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        A = self.assembler
        sk = config["skeleton"]
        if sk not in NATIVE_SKELETONS:
            raise ValueError(f"el esqueleto {sk} no tiene versión nativa ({', '.join(NATIVE_SKELETONS)})")
        full = dict(config)
        for p in A.skeletons[sk].params:
            full.setdefault(f"{sk}.{p}", A._skeleton_param(config, sk, p))
        if sk == "SA":  # configuraciones de antes del enfriamiento por tiempo (como en el Assembler)
            full["SA.cooling"] = config.get("SA.cooling", "iterations" if "SA.alpha" in config else full["SA.cooling"])
        for slot in ("constructor", "neighborhood", "perturbation"):
            name = config.get(slot)
            if name is not None:
                for p, v in A.registry.get(slot, name).default_params().items():
                    full.setdefault(f"{name}.{p}", v)
        shake = []
        if sk == "VNS":
            shake = [s.name for s in A.registry.compatible("neighborhood", sk) if s.name != config["neighborhood"]]
        return full, shake

    def assemble(self, config: dict[str, Any]):
        full, shake = self.full_config(config)

        def run(inst, rng: Random, budget: float) -> RunResult:
            best, obj, iters, secs = self.native.solve(self.model_of(inst), full, shake, rng.getrandbits(63), float(budget))
            return RunResult(best_solution=best, best_objective=obj, iterations=iters, elapsed_time=secs, accepted=0)

        return run


__all__ = ["NATIVE_SKELETONS", "NativeRunner"]
