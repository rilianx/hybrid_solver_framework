"""Tuning sobre el jobshop con el modelo C++ generado: el CLI genérico `tuning.cli` con su pack."""

from __future__ import annotations

from tuning.cli import main as _main

from .pack import PACK


def main(argv: list[str] | None = None) -> None:
    _main(PACK, argv)


if __name__ == "__main__":
    main()
