"""Tuning sobre el job shop: el CLI genérico `tuning.cli` con el pack del job shop.

    python -m examples.jobshop.tune --catalog handwritten --size 10x10 --trials 30 --ref-time 60
"""

from __future__ import annotations

from tuning.cli import main as _main

from .pack import PACK


def main(argv: list[str] | None = None) -> None:
    _main(PACK, argv)


if __name__ == "__main__":
    main()
