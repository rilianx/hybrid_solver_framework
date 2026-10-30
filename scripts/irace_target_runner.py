"""Target-runner para irace (§8): evalúa UNA configuración en UNA instancia.

irace lo invoca así (ver `tuning/irace_scenario.py`):

    target-runner <config_id> <instance_id> <seed> <instance_path> --skeleton=SA --SA.T0=12.5 ...

y espera en stdout un único número: el costo. Variables de entorno:
`HSF_BUDGET` (segundos por corrida, default 5), `HSF_PROBLEM` (paquete del problema, con
su `pack.PACK`; default `examples.lotsizing`), `HSF_GENERATED` (directorio de componentes
LLM a incluir en el catálogo; vacío = solo componentes a mano), `HSF_CATALOG` (como
`tuning.cli --catalog`; vacío = a mano + generados si hay), `HSF_SKELETONS` (separados por
espacio), `HSF_NATIVE=1` (correr en C++) y `HSF_OBJECTIVE=ratio` (costo / partida trivial, como
el objetivo de Optuna).
"""

from __future__ import annotations

import os
import sys
from random import Random


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print("uso: target-runner <config_id> <instance_id> <seed> <instance_path> [--param=valor ...]", file=sys.stderr)
        return 2
    _config_id, _instance_id, seed, instance_path = argv[:4]
    params = argv[4:]

    import importlib

    from tuning.cli import make_assembler
    from tuning.irace_scenario import parse_irace_params

    pack = importlib.import_module(os.environ.get("HSF_PROBLEM", "examples.lotsizing") + ".pack").PACK
    generated_dir = os.environ.get("HSF_GENERATED", "")
    catalog = os.environ.get("HSF_CATALOG") or ("all" if generated_dir else "handwritten")
    skeletons = os.environ.get("HSF_SKELETONS", "").split() or None
    assembler, _ = make_assembler(pack, catalog, generated_dir or None, skeletons=skeletons,
                                  native=os.environ.get("HSF_NATIVE") == "1")
    config = parse_irace_params(assembler.config_space(), params)
    inst = pack.load_instance(instance_path)
    budget = float(os.environ.get("HSF_BUDGET", "5"))
    norm = [pack.baseline_cost(inst)] if os.environ.get("HSF_OBJECTIVE") == "ratio" else None
    cost = assembler.evaluate(config, [inst], budget, seed=int(float(seed)) % (2**31), normalizers=norm)
    print(f"{cost:.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
