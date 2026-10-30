"""Genera componentes para el job shop con un LLM real: el CLI genérico `llm.cli` con el pack del job shop.

    python -m examples.jobshop.generate --from-scratch --slots greedy_score neighborhood destruction perturbation
"""

from __future__ import annotations

from llm.cli import main as _main

from .pack import PACK


def main(argv: list[str] | None = None) -> None:
    _main(PACK, argv)


if __name__ == "__main__":
    main()
