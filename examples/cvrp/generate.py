"""Genera componentes para el CVRP con un LLM real: el CLI genérico `llm.cli` con el pack del CVRP.

    python -m examples.cvrp.generate --from-scratch --slots greedy_score neighborhood destruction perturbation
"""

from __future__ import annotations

from llm.cli import main as _main

from .pack import PACK


def main(argv: list[str] | None = None) -> None:
    _main(PACK, argv)


if __name__ == "__main__":
    main()
