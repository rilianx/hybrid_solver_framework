"""Prompts compactos (`--compact-prompts`): en lugar del código completo de lo que el LLM solo usa (el modelo C++ en
los prompts de componentes, los componentes que ya están en el catálogo, `Rng` y `Config` del contrato, la clase de la instancia), sus prototipos:
declaraciones, firmas y comentarios. Lo que el LLM tiene que modificar (el componente o el modelo que se corrige u
optimiza) y el oráculo de la vista MIP (es la especificación) van siempre completos.
"""

from __future__ import annotations

import ast
import os
import re

ENV = "HSF_COMPACT_PROMPTS"


def compact_default() -> bool:
    return os.environ.get(ENV, "").lower() in ("1", "yes", "true")


def _skip_literal(src: str, i: int) -> int:
    """Desde un comentario o literal en `i`, el índice siguiente a su fin (o `i` si no empieza uno)."""
    if src.startswith("//", i):
        j = src.find("\n", i)
        return len(src) if j < 0 else j
    if src.startswith("/*", i):
        j = src.find("*/", i + 2)
        return len(src) if j < 0 else j + 2
    if src[i] in "\"'":
        q, j = src[i], i + 1
        while j < len(src) and src[j] != q:
            j += 2 if src[j] == "\\" else 1
        return j + 1
    return i


_BODY = re.compile(r"\)\s*(?:const\s*|override\s*|noexcept\s*|final\s*|->\s*[\w:<>,\s*&]+)*$")


def cpp_outline(src: str) -> str:
    """El código C++ sin los cuerpos de las funciones (quedan las declaraciones, las firmas y los comentarios). Los
    cuerpos de clases, structs y namespaces se conservan; el de una función se reconoce por la `)` que lo precede."""
    out, i, n = [], 0, len(src)
    while i < n:
        j = _skip_literal(src, i)
        if j != i:
            out.append(src[i:j])
            i = j
            continue
        c = src[i]
        if c == "{" and _BODY.search("".join(out)[-300:].rstrip()):
            depth, k = 0, i
            while k < n:
                k2 = _skip_literal(src, k)
                if k2 != k:
                    k = k2
                    continue
                depth += {"{": 1, "}": -1}.get(src[k], 0)
                if depth == 0:
                    break
                k += 1
            while out and out[-1].isspace():
                out.pop()
            out.append(";")
            m = re.match(r"[ \t]*(//[^\n]*)", src[i + 1:])  # el comentario de la línea de la firma se conserva
            if m:
                out.append("  " + m.group(1))
            i = k + 1
            if src[i:i + 1] == ";":
                i += 1
            continue
        out.append(c)
        i += 1
    text = "".join(out)
    return re.sub(r"\n{3,}", "\n\n", text)


def py_outline(src: str, drop: tuple[str, ...] = ("save",)) -> str:
    """La clase de la instancia con lo que el LLM necesita para leerla: los campos, las propiedades y métodos de acceso
    y `to_text` (define el formato). Se omiten los métodos estáticos y de clase (generadores, `parse`, `load`) y los
    de `drop`."""
    tree = ast.parse(src)
    lines = src.splitlines()
    cuts: list[tuple[int, int]] = []  # (primera línea, última), 1-indexadas

    def visit(node):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                deco = {d.id for d in child.decorator_list if isinstance(d, ast.Name)}
                if child.name in drop or deco & {"staticmethod", "classmethod"}:
                    cuts.append((min([child.lineno] + [d.lineno for d in child.decorator_list]), child.end_lineno))
            elif isinstance(child, ast.ClassDef):
                visit(child)

    visit(tree)
    for start, end in sorted(cuts, reverse=True):
        del lines[start - 1:end]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).rstrip() + "\n"
