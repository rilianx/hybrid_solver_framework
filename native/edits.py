"""Respuestas como ediciones: el LLM devuelve solo lo que cambia, como bloques "buscar / reemplazar" sobre el código
actual (como un editor de código), en vez del componente completo. La salida es lo que más cuesta en tokens, y en
una optimización o una corrección cambia una parte chica del componente.

    <<<<<<< BUSCAR
    texto exacto del código actual (que aparezca UNA sola vez)
    =======
    texto que lo reemplaza
    >>>>>>> REEMPLAZAR

Los bloques se aplican en orden, cada uno sobre el resultado del anterior. Si un texto a buscar no aparece o
aparece más de una vez, la edición falla y el error vuelve al LLM. Si la respuesta no trae bloques de edición
pero sí un bloque ```cpp```, se toma como el componente completo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

EDIT_INSTRUCTIONS = """Devuelve SOLO los cambios, como bloques de edición sobre el componente actual (como en un editor):

<<<<<<< BUSCAR
(texto exacto del componente actual, con el contexto justo para que aparezca UNA sola vez)
=======
(el texto que lo reemplaza)
>>>>>>> REEMPLAZAR

Puedes usar varios bloques; se aplican en orden. Para agregar código, busca la línea junto a la que va e inclúyela
también en el reemplazo. Copia el texto a buscar tal cual (espacios incluidos). Solo si de verdad conviene reescribir
casi todo, devuelve en su lugar el componente completo en un bloque ```cpp```."""

_EDIT = re.compile(r"<<<<<<< BUSCAR\n(.*?)\n?=======\n(.*?)\n?>>>>>>> REEMPLAZAR", re.DOTALL)


class EditError(ValueError):
    pass


@dataclass
class EditResult:
    source: str
    mode: str  # "edits" | "full"
    n_edits: int = 0


def find_edits(reply: str) -> list[tuple[str, str]]:
    return [(a, b) for a, b in _EDIT.findall(reply)]


def apply_edits(source: str, edits: list[tuple[str, str]]) -> str:
    out = source
    for k, (old, new) in enumerate(edits, 1):
        if not old.strip():
            raise EditError(f"el bloque {k} tiene el texto a buscar vacío")
        n = out.count(old)
        if n == 0:
            head = old.strip().splitlines()[0][:120]
            raise EditError(f"el bloque {k}: el texto a buscar no aparece en el código actual (empieza con «{head}»); "
                            "cópialo tal cual, con los mismos espacios")
        if n > 1:
            raise EditError(f"el bloque {k}: el texto a buscar aparece {n} veces; agrega contexto para que sea único")
        out = out.replace(old, new, 1)
    return out


def merge_reply(source: str, reply: str) -> EditResult:
    """La respuesta aplicada sobre `source`: ediciones si las trae, si no el componente completo. `EditError` si las
    ediciones no se pueden aplicar o si no hay ni ediciones ni código."""
    edits = find_edits(reply)
    if edits:
        return EditResult(apply_edits(source, edits), "edits", len(edits))
    from .generated import _BLOCK

    blocks = _BLOCK.findall(reply)
    if blocks:
        return EditResult(blocks[0].strip("\n") + "\n", "full")
    raise EditError("la respuesta no trae bloques de edición (<<<<<<< BUSCAR ... >>>>>>> REEMPLAZAR) ni un bloque ```cpp```")


__all__ = ["EDIT_INSTRUCTIONS", "EditError", "EditResult", "apply_edits", "find_edits", "merge_reply"]
