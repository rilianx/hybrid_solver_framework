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

from core.assembler import Assembler
from core.skeleton import RunResult

NATIVE_SKELETONS = ("SA", "ILS", "VNS", "TS", "PR", "HYB")  # HYB: ILS en C++ + sub-MIPs en Python


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
        for slot in ("constructor", "neighborhood", "perturbation", "relink", "destruction"):
            name = config.get(slot)
            if name is not None:
                for p, v in A.registry.get(slot, name).default_params().items():
                    full.setdefault(f"{name}.{p}", v)
        shake = []
        if sk == "VNS":
            shake = [s.name for s in A.registry.compatible("neighborhood", sk) if s.name not in (config["neighborhood"], "composite")]
        return full, shake

    def assemble(self, config: dict[str, Any]):
        full, shake = self.full_config(config)
        if full["skeleton"] == "HYB":
            return self._hybrid(full)

        def run(inst, rng: Random, budget: float) -> RunResult:
            best, obj, iters, secs = self.native.solve(self.model_of(inst), full, shake, rng.getrandbits(63), float(budget))
            return RunResult(best_solution=best, best_objective=obj, iterations=iters, elapsed_time=secs, accepted=0)

        return run


    def _hybrid(self, full: dict[str, Any]):
        """HYB: ILS con recocido en C++ (`solve_from`) alternado con sub-MIPs en Python (`skeletons/hybrid.py`)."""
        from core.common_components import MIPModelRepair
        from skeletons.hybrid import run_hybrid

        A = self.assembler
        inner = {k: v for k, v in full.items() if not k.startswith("HYB.") and k not in ("destruction", "skeleton")}
        inner.update({"skeleton": "ILS", "ILS.strength": full["HYB.strength"], "ILS.ls_sample": full["HYB.ls_sample"],
                      "ILS.ls_strategy": "best", "ILS.ls_time_share": 1.0, "ILS.accept": "anneal", "ILS.T_rel": full["HYB.T_rel"]})
        inner, _ = NativeRunner(A, self.native, self.model_of).full_config(inner)
        dname = full["destruction"]
        dspec = A.registry.get("destruction", dname)

        def run(inst, rng: Random, budget: float) -> RunResult:
            P = A.problem_factory(inst)
            m = self.model_of(inst)
            destr = dspec.make(P, **{p: full[f"{dname}.{p}"] for p in dspec.params if f"{dname}.{p}" in full})

            def local_search(sol, seconds, rng_):
                seed = rng_.getrandbits(63)
                if sol is None:
                    best, obj, iters, _ = self.native.solve(m, inner, [], seed, float(seconds))
                else:
                    best, obj, iters, _ = self.native.solve_from(m, inner, [], sol, seed, float(seconds))
                return best, obj, iters

            return run_hybrid(P, local_search, destr, MIPModelRepair(P), inst, rng, budget, ls_share=full["HYB.ls_share"],
                              mip_share=full["HYB.mip_share"], destroy_ratio=full["HYB.destroy_ratio"])

        return run


class NativeAssembler(Assembler):
    """Un `Assembler` cuyas configuraciones corren en C++: mismo espacio, mismos defaults y misma
    evaluación (`evaluate`, `config_space`, ...); solo cambia `assemble`. La factibilidad del resultado la
    sigue revisando el `problem_factory` de Python (un control cruzado más)."""

    def __init__(self, *args, native, model_of, **kwargs):
        super().__init__(*args, **kwargs)
        self.native, self.model_of = native, model_of

    def assemble(self, config: dict[str, Any]):
        return NativeRunner(self, self.native, self.model_of).assemble(config)


def native_pack(pack):
    """El pack con solo los componentes que existen en C++ (en los slots que corre C++) y los
    esqueletos nativos; `(pack, módulo nativo)`."""
    import importlib
    from dataclasses import replace

    if not pack.native_module:
        raise SystemExit(f"el problema {pack.name} no tiene backend nativo (ProblemPack.native_module)")
    mod = importlib.import_module(pack.native_module)
    names = mod.native.names()
    keep = []
    for comp, factory in pack.handwritten:
        slot = comp["slot"]
        if slot in names and comp["name"] not in names[slot]:
            continue
        keep.append((comp, factory))
    return replace(pack, handwritten=keep), mod


__all__ = ["NATIVE_SKELETONS", "NativeAssembler", "NativeRunner", "native_pack"]
