"""Target-runner para irace (§8): evalúa UNA configuración en UNA instancia.

irace lo invoca así (ver `tuning/irace_scenario.py`):

    target-runner <config_id> <instance_id> <seed> <instance_path> --skeleton=SA --SA.T0=12.5 ...

y espera en stdout un único número: el costo. Variables de entorno:
`HSF_BUDGET` (segundos por corrida, default 5), `HSF_PROBLEM` (paquete del problema, con
su `pack.PACK`; default `examples.lotsizing`), `HSF_GENERATED` (workspace de los componentes
C++ del LLM; vacío = el del problema), `HSF_SKELETONS` (separados por espacio), `HSF_SCALE_BUDGET=1` y
`HSF_OBJECTIVE=ratio` (costo / partida trivial).
"""

from __future__ import annotations

import os
import sys


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
    skeletons = os.environ.get("HSF_SKELETONS", "").split() or None
    assembler, _ = make_assembler(pack, os.environ.get("HSF_GENERATED") or None, skeletons=skeletons,
                                  scale_budget=os.environ.get("HSF_SCALE_BUDGET") == "1")
    config = parse_irace_params(assembler.config_space(), params)
    inst = pack.load_instance(instance_path)
    budget = float(os.environ.get("HSF_BUDGET", "5"))
    norm = [pack.baseline_cost(inst)] if os.environ.get("HSF_OBJECTIVE") == "ratio" else None
    cost = assembler.evaluate(config, [inst], budget, seed=int(float(seed)) % (2**31), normalizers=norm)
    print(f"{cost:.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
