"""Tuning sobre el CLSP (§8): el CLI genérico `tuning.cli` con el pack del CLSP.

    python -m examples.lotsizing.tune --trials 30 --budget 5 --train 3 --test 3 --catalog both
    python -m examples.lotsizing.tune --skeletons SA ILS VNS --ref-time 60 --size 10x15   # esqueleto fijo

Instancias Trigeiro (utilización 0,95, TBO 3); train y test con semillas disjuntas.
Ver `tuning/cli.py` para las opciones.
"""

from __future__ import annotations

from tuning.cli import main as _main

from .pack import PACK


def main(argv: list[str] | None = None) -> None:
    _main(PACK, argv)


if __name__ == "__main__":
    main()
