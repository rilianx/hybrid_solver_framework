"""Correr irace (R) como tuner, con el mismo espacio, las mismas instancias y la misma evaluación en test
que Optuna (`tuning.cli --tuner irace`).

irace llama al target-runner (`scripts/irace_target_runner.py`) por cada (configuración, instancia,
semilla); el costo que recibe es el mismo que el de un trial de Optuna con `--objective ratio`
(costo / costo de la partida trivial). Al terminar se lee la élite que imprime irace y la mejor
configuración pasa a la evaluación en test de `tuning.evaluation`, igual que la de Optuna.

Necesita R con el paquete irace (en Ubuntu: `apt install r-cran-irace`).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.assembler import describe

BEST_HEADER = "# Best configurations as commandlines"


def irace_executable() -> str:
    exe = shutil.which("irace")
    if exe:
        return exe
    try:
        lib = subprocess.run(["Rscript", "-e", 'cat(system.file(package="irace"))'], capture_output=True, text=True,
                             timeout=60).stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        lib = ""
    if lib and (Path(lib) / "bin" / "irace").exists():
        return str(Path(lib) / "bin" / "irace")
    raise SystemExit("no se encontró irace: instala R y el paquete irace (Ubuntu: apt install r-cran-irace)")


def parse_elites(stdout: str) -> list[list[str]]:
    """Las configuraciones élite en el orden de irace (la primera es la mejor), como listas de `--p=v`."""
    lines = stdout.splitlines()
    try:
        start = next(i for i, ln in enumerate(lines) if ln.startswith(BEST_HEADER))
    except StopIteration as exc:
        raise RuntimeError("irace no imprimió las mejores configuraciones:\n" + "\n".join(lines[-40:])) from exc
    out = []
    for ln in lines[start + 1:]:
        m = re.match(r"^\s*\d+\s+(--.*)$", ln)
        if not m:
            if out:
                break
            continue
        out.append(re.findall(r"--\S+?=(?:\"[^\"]*\"|\S+)", m.group(1)))
    return out


@dataclass
class IraceResult:
    best_config: dict[str, Any]
    elites: list[dict[str, Any]]
    best_cost: float
    seconds: float
    experiments: int
    log_tail: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tuner": "irace",
            "best_config": self.best_config,
            "best_cost": self.best_cost,
            "best_summary": describe(self.best_config),
            "n_trials": self.experiments,
            "n_failed": 0,
            "seconds": round(self.seconds, 1),
            "skeleton_usage": dict(Counter(e["skeleton"] for e in self.elites)),
            "elites": [describe(e) for e in self.elites],
            "elite_configs": self.elites,
            "reevaluated": [],
            "log_tail": self.log_tail,
        }


def tune_with_irace(assembler, scenario: Path, train, budget: float, max_experiments: int, seed: int = 0,
                    normalizers: list[float] | None = None, timeout: float | None = None) -> IraceResult:
    from tuning.irace_scenario import parse_irace_params

    space = assembler.config_space()
    scenario = Path(scenario).resolve()  # irace corre desde el directorio del escenario
    t0 = time.monotonic()
    cmd = [irace_executable(), "--scenario", str(scenario), "--seed", str(seed), "--max-experiments", str(max_experiments)]
    proc = subprocess.run(cmd, cwd=scenario.parent, capture_output=True, text=True, timeout=timeout)
    need = re.search(r"maxExperiments' of at least '(\d+)'", proc.stdout + proc.stderr)
    if proc.returncode != 0 and need:  # irace pide un mínimo según el espacio: se usa ese mínimo
        max_experiments = int(need.group(1))
        cmd[-1] = str(max_experiments)
        proc = subprocess.run(cmd, cwd=scenario.parent, capture_output=True, text=True, timeout=timeout)
    seconds = time.monotonic() - t0
    if proc.returncode != 0:
        raise RuntimeError(f"irace terminó con código {proc.returncode}:\n{(proc.stdout + proc.stderr)[-4000:]}")
    elites = [parse_irace_params(space, args) for args in parse_elites(proc.stdout)]
    best = elites[0]
    cost = assembler.evaluate(best, train, budget, seed=seed, normalizers=normalizers)
    return IraceResult(best, elites, cost, seconds, max_experiments, proc.stdout.splitlines()[-30:])


__all__ = ["IraceResult", "irace_executable", "parse_elites", "tune_with_irace"]
