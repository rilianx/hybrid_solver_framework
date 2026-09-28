"""Etapa `improve` sobre el CPMP de referencia (`llm.improver`), p.ej. mejorar la reducción de FRG
como fase, partiendo de la escrita a mano:

    python -m examples.cpmp.improve --slot phase --base reduce_stack --seed --context bg_fill,* --rounds 4
"""

from __future__ import annotations

from llm.improver import main as _main

from .pack import PACK


def main(argv: list[str] | None = None):
    return _main(PACK, argv, workspace="generated/cpmp_improve")


if __name__ == "__main__":
    main()
