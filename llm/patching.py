"""Reparación localizada: el LLM devuelve solo las definiciones que cambia y el framework las
reemplaza en el módulo por nombre.

Con componentes pesados o complejos, el error suele estar en una función (un `delta` que no
incluye la penalización, un `from_assignment` con un índice mal puesto). Pedir el módulo entero
para corregirlo gasta tokens y arriesga romper lo que ya pasaba; pedir solo lo que cambia no.

Reglas de `apply_patch(módulo, parche)`:
- una función de nivel superior del parche reemplaza la del mismo nombre (o se agrega al final);
- una clase que ya existe se parchea método por método (y atributo por atributo): los métodos del
  parche reemplazan a los del mismo nombre y los nuevos se agregan al final de la clase; una clase
  nueva se agrega entera;
- una asignación de nivel superior (`COMPONENT = …`, una constante) reemplaza la del mismo nombre o
  se agrega antes de la primera definición;
- los imports que falten se agregan después de los imports existentes;
- otras sentencias se agregan al final.

Si el parche define todos los nombres `required` (p.ej. `COMPONENT` y `build_component`), es un
módulo completo y reemplaza al anterior. Si no se puede parsear o aplicar, `merge_reply` lo usa
tal cual (como antes: el validador informará el error). El módulo resultante siempre se vuelve a
validar entero.
"""

from __future__ import annotations

import ast
import textwrap
from dataclasses import dataclass, field

PATCH_INSTRUCTIONS = (
    "Devuelve SOLO lo que cambias, en un único bloque ```python```: las funciones completas que reescribes (con el mismo "
    "nombre), los métodos que reescribes dentro de `class <MismaClase>:` (solo esos métodos, no la clase entera), las "
    "funciones o constantes auxiliares nuevas y los imports que agregues. El resto del módulo queda tal cual: cada "
    "definición se reemplaza por nombre y después se vuelve a validar el módulo entero. Devuelve el módulo completo solo "
    "si de verdad hay que reescribirlo todo."
)


class PatchError(ValueError):
    pass


@dataclass
class PatchResult:
    source: str
    mode: str  # "patch" | "full"
    replaced: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)


def _span(node: ast.AST) -> tuple[int, int]:
    start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
    return start, node.end_lineno


def _text(lines: list[str], node: ast.AST) -> str:
    s, e = _span(node)
    return textwrap.dedent("".join(lines[s - 1:e]))


def _assigned(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Assign):
        return tuple(t.id for t in node.targets if isinstance(t, ast.Name))
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return (node.target.id,)
    return ()


def _key(node: ast.AST) -> str | None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    names = _assigned(node)
    return ",".join(names) if names else None


def _is_placeholder(node: ast.AST) -> bool:
    """`...`, `pass` o un docstring suelto dentro de una clase del parche."""
    return isinstance(node, ast.Pass) or (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))


def _lines(src: str) -> list[str]:
    lines = src.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    return lines


def defined_names(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    out: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
        out.update(_assigned(node))
    return out


def apply_patch(source: str, patch: str, required: tuple[str, ...] = ()) -> PatchResult:
    try:
        ptree = ast.parse(patch)
    except SyntaxError as exc:
        raise PatchError(f"el parche no parsea: {exc}") from exc
    if required and set(required) <= defined_names(patch):
        return PatchResult(patch, "full")
    try:
        otree = ast.parse(source)
    except SyntaxError:
        return PatchResult(patch, "full")
    olines, plines = _lines(source), _lines(patch)
    top = {_key(n): n for n in otree.body if _key(n)}
    imports = [n for n in otree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    have_imports = {ast.dump(n) for n in imports}
    first_def = next((_span(n)[0] for n in otree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))),
                     len(olines) + 1)
    after_imports = imports[-1].end_lineno + 1 if imports else 1
    # ediciones sobre líneas del original: (posición, tipo, orden, inicio, fin, texto). Reemplazo (tipo 1):
    # líneas [inicio, fin]; inserción (tipo 0): antes de la línea `inicio`. Se aplican de abajo hacia
    # arriba; en la misma línea, el reemplazo antes que la inserción, y las inserciones en su orden.
    edits: list[tuple[int, int, int, int, int, str]] = []
    res = PatchResult("", "patch")

    def replace(node, text):
        s, e = _span(node)
        edits.append((s, 1, len(edits), s, e, text))

    def insert(before_line, text):
        edits.append((before_line, 0, len(edits), before_line, before_line - 1, text))

    for node in ptree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if ast.dump(node) not in have_imports:
                insert(after_imports, _text(plines, node))
                res.added.append(f"import {', '.join(a.name for a in node.names)}")
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue  # docstring del parche
        key = _key(node)
        old = top.get(key) if key else None
        if isinstance(node, ast.ClassDef) and isinstance(old, ast.ClassDef):
            _patch_class(old, node, olines, plines, replace, insert, res)
            continue
        text = _text(plines, node)
        if old is not None:
            replace(old, text)
            res.replaced.append(key)
        elif _assigned(node):
            insert(min(first_def, len(olines) + 1), text + "\n\n")
            res.added.append(key)
        else:
            insert(len(olines) + 1, "\n\n" + text)
            res.added.append(key or type(node).__name__)
    out = list(olines)
    for _pos, _kind, _seq, s, e, text in sorted(edits, reverse=True):
        out[s - 1:e] = [text if text.endswith("\n") else text + "\n"]
    new = "".join(out)
    try:
        ast.parse(new)
    except SyntaxError as exc:
        raise PatchError(f"el módulo parchado no parsea: {exc}") from exc
    res.source = new
    return res


def _patch_class(old: ast.ClassDef, new: ast.ClassDef, olines, plines, replace, insert, res: PatchResult) -> None:
    members = {_key(n): n for n in old.body if _key(n)}
    indent = " " * old.body[0].col_offset
    for node in new.body:
        if _is_placeholder(node):
            continue
        key = _key(node)
        text = textwrap.indent(_text(plines, node), indent)
        target = members.get(key) if key else None
        if target is not None:
            replace(target, text)
            res.replaced.append(f"{old.name}.{key}")
        else:
            insert(old.end_lineno + 1, "\n" + text)
            res.added.append(f"{old.name}.{key or type(node).__name__}")


def merge_reply(previous: str | None, reply: str, required: tuple[str, ...] = ()) -> PatchResult:
    """La respuesta a un pedido de corrección aplicada sobre el código rechazado. Sin código previo, o
    si el parche no se puede aplicar, la respuesta se usa tal cual (y el validador dirá qué falla)."""
    if previous is None:
        return PatchResult(reply, "full")
    try:
        return apply_patch(previous, reply, required)
    except PatchError:
        return PatchResult(reply, "full")


__all__ = ["PATCH_INSTRUCTIONS", "PatchError", "PatchResult", "apply_patch", "defined_names", "merge_reply"]
