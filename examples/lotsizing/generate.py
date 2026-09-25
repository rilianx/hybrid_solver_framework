"""Genera componentes para el CLSP con un LLM real: el CLI genérico `llm.cli` con el pack del CLSP.

    export OPENAI_API_KEY=...
    python -m examples.lotsizing.generate --slots neighborhood destruction --n 3
    python -m examples.lotsizing.generate --from-scratch --planner --workspace generated/clsp_scratch \
        --slots greedy_score neighborhood destruction perturbation

Ver `llm/cli.py` para las opciones.
"""

from __future__ import annotations

from llm.cli import main as _main

from .pack import PACK


def main(argv: list[str] | None = None) -> None:
    _main(PACK, argv)


if __name__ == "__main__":
    main()
