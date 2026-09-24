"""Escenario irace completo a partir del `ConfigSpace` (§8).

irace corre en R; aquí no se ejecuta, se **prepara**: `parameters.txt` (ya
existía el exportador), `instances.txt`, `scenario.txt` y el target-runner que
irace invoca por cada (configuración, instancia, semilla). Con eso:

    irace --scenario tuning_out/irace/scenario.txt

Todas las rutas del escenario son relativas: irace (≥ 3.0) las resuelve respecto del
directorio de `scenario.txt`, y el target-runner sube desde su propia ubicación hasta la
raíz del repo. Así el escenario generado en un runner de GitHub Actions corre igual en
otra máquina con el repo clonado.

`parse_irace_params` convierte los `--nombre=valor` que irace pasa al
target-runner en una configuración tipada según el espacio, así el mismo
`Assembler.evaluate` sirve para Optuna y para irace.
"""

from __future__ import annotations

import os
import shlex
from pathlib import Path
from typing import Any

from config_space import ConfigSpace, to_irace_parameters


def parse_irace_params(space: ConfigSpace, argv: list[str]) -> dict[str, Any]:
    """`["--skeleton=SA", "--SA.T0=12.5", ...]` -> config tipada. irace pasa también
    `--name value` separados; se aceptan ambas formas."""
    nodes = {n.name: n for n in space.nodes}
    raw: dict[str, str] = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok.startswith("--"):
            if "=" in tok:
                k, v = tok[2:].split("=", 1)
            else:
                k, v = tok[2:], argv[i + 1] if i + 1 < len(argv) else ""
                i += 1
            raw[k] = v.strip().strip('"')
        i += 1
    config: dict[str, Any] = {}
    for k, v in raw.items():
        node = nodes.get(k)
        if node is None:
            raise ValueError(f"parámetro desconocido para el espacio: {k}")
        if node.type == "int":
            config[k] = int(round(float(v)))
        elif node.type == "float":
            config[k] = float(v)
        elif node.type == "bool":
            config[k] = v.upper() in ("TRUE", "1", "T", "YES")
        else:
            config[k] = v
    return space.fold(config)


def write_irace_scenario(
    space: ConfigSpace,
    out_dir: str | Path,
    instance_paths: list[str | Path],
    budget: float,
    max_experiments: int = 300,
    target_runner_module: str = "scripts.irace_target_runner",
    generated_dir: str | None = None,
) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "parameters.txt").write_text(to_irace_parameters(space))
    # instancias dentro del escenario: relativas a trainInstancesDir; si alguna está fuera, absolutas
    paths = [Path(p).resolve() for p in instance_paths]
    inst_dir = out.resolve() / "instances"
    if all(inst_dir in p.parents for p in paths):
        inst_dir_entry, lines = "./instances", [p.relative_to(inst_dir).as_posix() for p in paths]
    else:
        inst_dir_entry, lines = "", [str(p) for p in paths]
    (out / "instances.txt").write_text("\n".join(lines) + "\n")
    runner = out / "target-runner"
    env = f"export HSF_BUDGET={budget}\n" + (f"export HSF_GENERATED={shlex.quote(generated_dir)}\n" if generated_dir else "")
    root = Path(os.path.relpath(Path.cwd().resolve(), out.resolve())).as_posix()
    runner.write_text(
        "#!/usr/bin/env bash\n"
        "# irace llama: target-runner <config_id> <instance_id> <seed> <instance> [--param=valor ...]\n"
        "set -euo pipefail\n"
        f"cd \"$(dirname \"$0\")/{root}\"  # raíz del repo\n"
        f"{env}"
        f"exec python -W ignore -m {target_runner_module} \"$@\"\n"
    )
    runner.chmod(0o755)
    (out / "scenario.txt").write_text(
        "## Escenario irace generado por tuning.irace_scenario (rutas relativas a este archivo)\n"
        'parameterFile = "./parameters.txt"\n'
        f'trainInstancesDir = "{inst_dir_entry}"\n'
        'trainInstancesFile = "./instances.txt"\n'
        'targetRunner = "./target-runner"\n'
        'execDir = "./exec"\n'
        f"maxExperiments = {max_experiments}\n"
        "deterministic = 0\n"
        "digits = 4\n"
    )
    (out / "exec").mkdir(exist_ok=True)
    return out / "scenario.txt"
