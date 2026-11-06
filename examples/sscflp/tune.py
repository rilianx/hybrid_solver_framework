"""Tuning sobre el SSCFLP: el CLI genérico `tuning.cli` con el pack del SSCFLP.

    python -m examples.sscflp.tune --size 20x100 --trials 30 --tuner irace
"""

from __future__ import annotations

from tuning.cli import main as _main

from .pack import PACK


def main(argv: list[str] | None = None) -> None:
    _main(PACK, argv)


if __name__ == "__main__":
    main()
