"""Genera el `ProblemModel` del CPMP con un LLM, desde la descripción y los casos de prueba: vista
heurística y vista constructiva, sin vista MIP (el CLI genérico `llm.model_cli`).

    python -m examples.cpmp.generate_model --provider anthropic
    python -m examples.cpmp.generate --problem-model generated/cpmp_model/problem_model/model_constructive_r1.py --slots greedy_score
    python -m examples.cpmp.tune --problem-model generated/cpmp_model/problem_model/model_constructive_r1.py --catalog all
"""

from __future__ import annotations

from llm.model_cli import main as _main

from .pack import PACK


def main(argv: list[str] | None = None) -> None:
    _main(PACK, argv)


if __name__ == "__main__":
    main()
