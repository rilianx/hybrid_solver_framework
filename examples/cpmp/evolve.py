"""Etapa `evolve` sobre el CPMP de referencia (`llm.evolve`): desde la máquina mínima (sin ver FRG)
o desde FRG como semilla:

    python -m examples.cpmp.evolve --rounds 12
    python -m examples.cpmp.evolve --seed frg_machine --rounds 8
"""

from __future__ import annotations

from llm.evolve import main as _main

from .pack import PACK


def main(argv: list[str] | None = None):
    return _main(PACK, argv, workspace="generated/cpmp_evolve")


if __name__ == "__main__":
    main()
