"""Genera el `ProblemModel` del CLSP con un LLM (§6.1) y lo compara con el escrito a mano.

    python -m examples.lotsizing.generate_model --rounds 4
"""

from __future__ import annotations

from llm.model_cli import main as _main

from .pack import PACK


def main(argv: list[str] | None = None) -> None:
    _main(PACK, argv)


if __name__ == "__main__":
    main()
