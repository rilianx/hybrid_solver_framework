"""Exportador de `ConfigSpace` al formato `parameters.txt` de irace (§8).

Formato de irace (una línea por parámetro):

    <name> <switch> <type> (<domain>) [| <condition>]

- type: "i" (entero), "r" (real), "c" (categórico), "o" (ordinal).
- log-scale no es un tipo nativo de irace; se deja documentado como
  comentario `# log-scale` junto al parámetro para que quien arme el
  `target-runner` haga el remuestreo (o para migrarlo a una versión de
  irace que sí lo soporte nativamente).
"""

from __future__ import annotations

from .space import ConfigSpace, ParamNode


def _irace_type(node: ParamNode) -> str:
    return {"int": "i", "float": "r", "cat": "c", "bool": "c"}[node.type]


def _irace_domain(node: ParamNode) -> str:
    if node.type in ("int", "float"):
        lo, hi = node.range
        return f"({lo}, {hi})"
    values = node.values if node.type != "bool" else ("TRUE", "FALSE")
    quoted = ", ".join(f'"{v}"' for v in values)
    return f"({quoted})"


def _irace_condition(node: ParamNode) -> str:
    if not node.conditions:
        return ""
    exprs = [c.as_irace_expr() for c in node.conditions]
    return " | " + " & ".join(exprs)


def to_irace_parameters(space: ConfigSpace) -> str:
    """Genera el contenido completo de un `parameters.txt` de irace."""
    lines = [
        "# Generado automáticamente por config_space.irace_export.to_irace_parameters",
        "# name switch type domain [| condition]",
    ]
    for node in space.nodes:
        switch = f'"--{node.name}="'
        comment = "  # log-scale" if node.log else ""
        lines.append(
            f"{node.name} {switch} {_irace_type(node)} {_irace_domain(node)}{_irace_condition(node)}{comment}"
        )
    return "\n".join(lines) + "\n"
