"""Tuning sobre el CPMP (esqueleto CONSTRUCT): el CLI genérico `tuning.cli` con el pack del CPMP.

    python -m examples.cpmp.tune --catalog handwritten --size 5x5 --trials 30 --budget 5
"""

from __future__ import annotations

from tuning.cli import main as _main

from .pack import PACK


def main(argv: list[str] | None = None) -> None:
    _main(PACK, argv)


if __name__ == "__main__":
    main()
