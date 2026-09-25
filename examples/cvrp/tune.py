"""Tuning sobre el CVRP: el CLI genérico `tuning.cli` con el pack del CVRP.

    python -m examples.cvrp.tune --catalog handwritten --size 30 --trials 30 --ref-time 60
"""

from __future__ import annotations

from tuning.cli import main as _main

from .pack import PACK


def main(argv: list[str] | None = None) -> None:
    _main(PACK, argv)


if __name__ == "__main__":
    main()
