"""Extrae los módulos Python de una respuesta del LLM y los materializa en disco.

Cada bloque ```python``` se guarda como `<workspace>/<slot>/<name>_r<round>.py`,
donde `name` sale de `COMPONENT["name"]` leído por AST (sin ejecutar el
módulo: eso lo hace la capa sintáctica del validador, en aislamiento).
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

_BLOCK = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)


@dataclass
class ParsedModule:
    source: str
    name: str | None  # COMPONENT["name"] si se pudo leer estáticamente
    path: Path | None = None


def extract_code_blocks(text: str) -> list[str]:
    blocks = [b.strip("\n") + "\n" for b in _BLOCK.findall(text)]
    if not blocks and re.search(r"^\s*COMPONENT\s*=", text, re.MULTILINE):
        # respuesta sin fences: se toma el texto completo como un único módulo
        blocks = [text.strip("\n") + "\n"]
    return blocks


def component_name(source: str) -> str | None:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "COMPONENT" for t in node.targets):
            try:
                value = ast.literal_eval(node.value)
            except Exception:  # noqa: BLE001
                return None
            if isinstance(value, dict):
                name = value.get("name")
                return str(name) if name else None
    return None


def parse_response(text: str) -> list[ParsedModule]:
    return [ParsedModule(source=src, name=component_name(src)) for src in extract_code_blocks(text)]


_SAFE = re.compile(r"[^a-zA-Z0-9_]+")


def materialize(modules: list[ParsedModule], workspace: Path, slot: str, round_no: int) -> list[ParsedModule]:
    directory = Path(workspace) / slot
    directory.mkdir(parents=True, exist_ok=True)
    for k, m in enumerate(modules):
        base = _SAFE.sub("_", m.name or f"unnamed_{k}")
        m.path = directory / f"{base}_r{round_no}.py"
        m.path.write_text(m.source)
    return modules
