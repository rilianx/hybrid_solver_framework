"""Exportador de `ConfigSpace` a un espacio *define-by-run* de Optuna (§8).

Optuna no tiene un formato estático como irace: el espacio condicional
se expresa llamando a `trial.suggest_*` solo para los parámetros que
resultan activos dado lo ya muestreado. `suggest_from_space` hace
exactamente eso, resolviendo las dependencias en el orden que haga
falta (no asume que `space.nodes` está topológicamente ordenado).

`trial` solo necesita exponer `suggest_int`, `suggest_float` y
`suggest_categorical` con la firma estándar de Optuna, así que esto
funciona con un `optuna.trial.Trial` real o con un doble de prueba.
"""

from __future__ import annotations

from typing import Any, Protocol

from .space import ConfigSpace, ParamNode


class OptunaTrialLike(Protocol):
    def suggest_int(self, name: str, low: int, high: int, *, log: bool = False) -> int: ...

    def suggest_float(self, name: str, low: float, high: float, *, log: bool = False) -> float: ...

    def suggest_categorical(self, name: str, choices: list[Any]) -> Any: ...


def _suggest_value(trial: OptunaTrialLike, node: ParamNode) -> Any:
    if node.type == "int":
        lo, hi = node.range
        return trial.suggest_int(node.name, int(lo), int(hi), log=node.log)
    if node.type == "float":
        lo, hi = node.range
        return trial.suggest_float(node.name, float(lo), float(hi), log=node.log)
    if node.type == "cat":
        return trial.suggest_categorical(node.name, list(node.values))
    if node.type == "bool":
        return trial.suggest_categorical(node.name, [True, False])
    raise ValueError(f"tipo de parámetro no soportado: {node.type}")


def suggest_from_space(space: ConfigSpace, trial: OptunaTrialLike) -> dict[str, Any]:
    """Muestrea una configuración completa, respetando condiciones (parent -> child).

    Un nodo cuyo padre quedó *resuelto mas no activo* (p.ej. `perturbation`
    cuando el `skeleton` muestreado no fue "ILS") se marca como resuelto e
    inactivo en cascada, no como "pendiente para siempre": de lo contrario
    cualquier rama del árbol condicional que no se activa en un muestreo
    dado dejaría nodos sin resolver y dispararía el error de abajo.
    """
    assignment: dict[str, Any] = {}
    resolved: set[str] = set()
    pending = list(space.nodes)

    while pending:
        made_progress = False
        still_pending: list[ParamNode] = []
        for node in pending:
            parents_resolved = all(c.parent in resolved for c in node.conditions)
            if not parents_resolved:
                still_pending.append(node)
                continue
            made_progress = True
            if node.is_active(assignment):
                assignment[node.name] = _suggest_value(trial, node)
            # si no está activo, simplemente no se agrega al assignment,
            # pero igual queda "resuelto" para que sus hijos se desactiven en cascada.
            resolved.add(node.name)
        pending = still_pending
        if not made_progress and pending:
            unresolved = ", ".join(n.name for n in pending)
            raise RuntimeError(
                f"no se pudieron resolver condiciones (¿referencian un parámetro inexistente?): {unresolved}"
            )

    return assignment
