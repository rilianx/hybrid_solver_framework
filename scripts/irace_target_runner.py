"""Target-runner para irace (§8): evalúa UNA configuración en UNA instancia.

irace lo invoca así (ver `tuning/irace_scenario.py`):

    target-runner <config_id> <instance_id> <seed> <instance_path> --skeleton=SA --SA.T0=12.5 ...

y espera en stdout un único número: el costo. Variables de entorno:
`HSF_BUDGET` (segundos por corrida, default 5) y `HSF_GENERATED` (directorio de
componentes LLM a incluir en el catálogo; vacío = solo componentes a mano).
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

    from core.assembler import Assembler
    from examples.lotsizing.catalog import build_registry, load_generated
    from examples.lotsizing.problem_model import CLSPInstance, LotSizingModel
    from tuning.irace_scenario import parse_irace_params

    generated_dir = os.environ.get("HSF_GENERATED", "")
    generated = load_generated(generated_dir, verbose=False) if generated_dir else []
    assembler = Assembler(problem_factory=LotSizingModel, registry=build_registry(generated))
    config = parse_irace_params(assembler.config_space(), params)
    inst = CLSPInstance.load(instance_path)
    budget = float(os.environ.get("HSF_BUDGET", "5"))
    cost = assembler.evaluate(config, [inst], budget, seed=int(float(seed)) % (2**31))
    print(f"{cost:.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
