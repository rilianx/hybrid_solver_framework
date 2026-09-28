"""Genera puntajes constructivos para el CPMP con un LLM real: el CLI genérico `llm.cli` con el pack del CPMP.

    python -m examples.cpmp.generate --from-scratch --slots greedy_score --n 3
"""

from __future__ import annotations

from llm.cli import main as _main

from .pack import PACK


def main(argv: list[str] | None = None) -> None:
    _main(PACK, argv)


if __name__ == "__main__":
    main()
