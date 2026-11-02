"""Tuning sobre el PFSP con flowtime total: el CLI genérico `tuning.cli` con el pack del flow shop."""

from __future__ import annotations

from tuning.cli import main as _main

from .pack import PACK


def main(argv: list[str] | None = None) -> None:
    _main(PACK, argv)


if __name__ == "__main__":
    main()
