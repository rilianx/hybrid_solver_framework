"""Las piezas de un problema con su vista MIP: el oráculo de referencia (`examples/<problema>/model_parts.py`) y la
vista MIP que escribió el LLM (`generated/<problema>_native/mip/mip.py`, ya validada). Para los tests que necesitan
una vista MIP conocida."""

from __future__ import annotations

from pathlib import Path

PACKS = {"clsp": "examples.lotsizing", "jobshop": "examples.jobshop", "cvrp": "examples.cvrp"}


def full_parts(problem: str):
    import importlib

    from core.packs import load_mip, with_mip

    oracle = importlib.import_module(f"{PACKS[problem]}.model_parts")
    return with_mip(oracle, load_mip(Path("generated") / f"{problem}_native" / "mip" / "mip.py"))


def mip_source(problem: str) -> str:
    return (Path("generated") / f"{problem}_native" / "mip" / "mip.py").read_text()
