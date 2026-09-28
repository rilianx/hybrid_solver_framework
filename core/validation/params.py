"""Parámetros extraíbles de un componente generado: lo que el LLM decide con un número tiene que
poder afinarlo el tuner junto con los demás hiperparámetros.

- `constants_check`: no hay constantes sueltas en el código (un umbral `0.3` escrito en una
  transición no lo ve el tuner). Se permiten 0, ±1, 2, tolerancias (|x| < 1e-3) y potencias de
  10 desde 100, que se usan para ordenar lexicográficamente o como centinela ("muy alto"). No
  cuentan el dict `COMPONENT` ni los valores por defecto de los argumentos (son los defaults de
  los parámetros).
- `params_check`: cada parámetro declarado trae `default`, `build_component` lo acepta, y cambia
  alguna construcción en las micro-instancias o la sonda (con los extremos de su rango, o cada
  valor): un parámetro inerte solo agranda el espacio del tuner.
"""

from __future__ import annotations

import ast
import inspect
import math
from random import Random
from typing import Any, Callable

from .base import CheckResult, fail, ok

LAYER = "syntactic"


def _allowed(x: float) -> bool:
    if isinstance(x, bool):
        return True
    a = abs(x)
    if a in (0, 1, 2) or a < 1e-3:
        return True
    if a >= 100:
        e = math.log10(a)
        return abs(e - round(e)) < 1e-9
    return False


def loose_constants(source: str) -> list[tuple[int, float]]:
    """(línea, valor) de cada número suelto del módulo, fuera de COMPONENT y de los defaults."""
    tree = ast.parse(source)
    skip: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "COMPONENT" for t in node.targets):
            skip |= {id(n) for n in ast.walk(node.value)}
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            for d in [*node.args.defaults, *[d for d in node.args.kw_defaults if d is not None]]:
                skip |= {id(n) for n in ast.walk(d)}
        if isinstance(node, (ast.Subscript,)):  # índices: x[0], x[-1], x[2:]
            skip |= {id(n) for n in ast.walk(node.slice)}
    out = []
    for node in ast.walk(tree):
        if id(node) in skip or not isinstance(node, ast.Constant):
            continue
        v = node.value
        if isinstance(v, (int, float)) and not isinstance(v, bool) and not _allowed(v):
            out.append((node.lineno, v))
    return sorted(set(out))


def constants_check(module) -> CheckResult:
    try:
        source = inspect.getsource(module)
    except (OSError, TypeError):
        return ok(LAYER, "no_loose_constants", "sin fuente")
    found = loose_constants(source)
    if found:
        shown = ", ".join(f"{v:g} (línea {ln})" for ln, v in found[:12])
        return fail(LAYER, "no_loose_constants",
                    f"números sueltos en el código: {shown}. Todo número que decide algo (umbral, peso, tope, desempate) va en "
                    f"COMPONENT['params'] con 'range' y 'default', y llega por build_component(problem, **params), para que el "
                    f"tuner lo afine. Se permiten 0, ±1, 2, tolerancias (< 1e-3) y potencias de 10 desde 100 (orden "
                    f"lexicográfico o centinela).")
    return ok(LAYER, "no_loose_constants")


def _alternatives(spec: dict) -> list:
    t = spec["type"]
    if t == "bool":
        return [True, False]
    if t == "cat":
        return list(spec["values"])
    lo, hi = spec["range"]
    return [int(lo), int(hi)] if t == "int" else [float(lo), float(hi)]


def params_check(component: dict, factory: Callable, instances_problems: list[tuple[Any, Any]],
                 signature: Callable[[Any, Any, Any], Any]) -> list[CheckResult]:
    """`instances_problems`: [(instancia, problema)]; `signature(impl, problem, inst)`: lo que el
    componente produce ahí (p.ej. las acciones del greedy)."""
    params = component.get("params") or {}
    if not params:
        return [ok(LAYER, "params_matter", "sin parámetros")]
    missing = [p for p, s in params.items() if "default" not in s]
    if missing:
        return [fail(LAYER, "params_default", f"los parámetros {missing} no declaran 'default' en COMPONENT['params']: el "
                                              f"default es el valor que propones y el punto de partida del tuner")]
    defaults = {p: s["default"] for p, s in params.items()}
    inst0, P0 = instances_problems[0]
    try:
        factory(P0, **defaults)
    except TypeError as exc:
        return [fail(LAYER, "params_accepted", f"build_component(problem, **params) no acepta los parámetros declarados: {exc}")]

    def sigs(values: dict) -> list:
        return [signature(factory(P, **values), P, inst) for inst, P in instances_problems]

    base = sigs(defaults)
    inert = []
    for p, spec in params.items():
        alts = [v for v in _alternatives(spec) if v != spec["default"]]
        if not any(sigs({**defaults, p: v}) != base for v in alts):
            inert.append(p)
    if inert:
        return [fail(LAYER, "params_matter",
                     f"los parámetros {inert} no cambian ninguna construcción (probados en los extremos de su rango, o cada "
                     f"valor, en las micro-instancias y la sonda): úsalos donde deciden algo o quítalos")]
    return [ok(LAYER, "params_matter", f"los {len(params)} parámetros cambian alguna construcción")]


def machine_signature(impl, problem, inst):
    from core.machine import MachinePolicy, machine_trace

    return [(s, repr(a)) for s, a in machine_trace(MachinePolicy(impl), problem.construction_view(inst), max_steps=20_000)]


__all__ = ["loose_constants", "constants_check", "params_check", "machine_signature"]
