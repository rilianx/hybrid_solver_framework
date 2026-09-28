"""Parámetros extraíbles de un componente generado: lo que el LLM decide con un número tiene que
poder afinarlo el tuner junto con los demás hiperparámetros.

- `normalize_machine_file`: antes de validar una máquina generada, el framework la NORMALIZA en
  vez de rechazarla (corrida 65: 8 de 12 máquinas rechazadas por un `10` o un `0.5` sueltos):
  `extract_constants` convierte cada número suelto de los métodos de la clase en un parámetro
  (`self._auto_<método>_k<i>`, declarado en COMPONENT con rango [0, 2·valor] y el valor como
  default); los parámetros sin default toman el de la firma de `build_component`; y los que no
  cambian ninguna construcción se sacan de COMPONENT (siguen con su default). Lo que queda
  fuera de los métodos (funciones de módulo, atributos de clase) lo sigue marcando
  `constants_check`.

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


AUTO = "_auto_"


def _skipped(tree) -> set[int]:
    """Nodos que no cuentan como números sueltos: COMPONENT, los defaults de argumentos, los índices
    y los parámetros que ya extrajo el framework (`_AUTO`, `_auto_*`)."""
    skip: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and (t.id in ("COMPONENT", "_AUTO") or t.id.startswith(AUTO))
                                                for t in node.targets):
            skip |= {id(n) for n in ast.walk(node.value)}
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            for d in [*node.args.defaults, *[d for d in node.args.kw_defaults if d is not None]]:
                skip |= {id(n) for n in ast.walk(d)}
        if isinstance(node, (ast.Subscript,)):  # índices: x[0], x[-1], x[2:]
            skip |= {id(n) for n in ast.walk(node.slice)}
    return skip


def loose_constants(source: str) -> list[tuple[int, float]]:
    """(línea, valor) de cada número suelto del módulo, fuera de COMPONENT y de los defaults."""
    tree = ast.parse(source)
    skip = _skipped(tree)
    out = []
    for node in ast.walk(tree):
        if id(node) in skip or not isinstance(node, ast.Constant):
            continue
        v = node.value
        if isinstance(v, (int, float)) and not isinstance(v, bool) and not _allowed(v):
            out.append((node.lineno, v))
    return sorted(set(out))


def _machine_class(tree) -> ast.ClassDef | None:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and any(
                isinstance(b, (ast.Assign, ast.AnnAssign)) and any(getattr(t, "id", None) == "states"
                                                                   for t in (b.targets if isinstance(b, ast.Assign) else [b.target]))
                for b in node.body):
            return node
    return None


def _range_for(v) -> dict:
    if isinstance(v, int):
        lo, hi = (0, 2 * v) if v > 0 else (2 * v, 0)
        return {"type": "int", "range": [lo, hi], "default": v}
    lo, hi = (0.0, 2.0 * v) if v > 0 else (2.0 * v, 0.0)
    return {"type": "float", "range": [lo, hi], "default": v}


def _set_component(tree, component: dict) -> None:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "COMPONENT" for t in node.targets):
            node.value = ast.parse(repr(component), mode="eval").body
            return


def _component_of(tree) -> dict | None:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "COMPONENT" for t in node.targets):
            try:
                return ast.literal_eval(node.value)
            except Exception:  # noqa: BLE001
                return None
    return None


_WRAPPER = '''
def build_component(problem, **params):
    """Envoltura del framework: los números que el LLM dejó sueltos en los métodos son parámetros
    (`_AUTO`, declarados en COMPONENT); se fijan en la clase mientras se construye (por si
    `__init__` los usa) y en la instancia."""
    auto = {k: params.pop(k, v) for k, v in _AUTO.items()}
    saved = {k: getattr(_MACHINE, "_auto_" + k) for k in auto}
    for k, v in auto.items():
        setattr(_MACHINE, "_auto_" + k, v)
    try:
        obj = _build_component_llm(problem, **params)
    finally:
        for k, v in saved.items():
            setattr(_MACHINE, "_auto_" + k, v)
    for k, v in auto.items():
        setattr(obj, "_auto_" + k, v)
    return obj
'''


def extract_constants(source: str) -> tuple[str, dict]:
    """(fuente nueva, {parámetro: especificación}): cada número suelto dentro de un método de la
    clase de la máquina pasa a ser `self._auto_<método>_k<i>` y un parámetro de COMPONENT."""
    tree = ast.parse(source)
    cls = _machine_class(tree)
    comp = _component_of(tree)
    if cls is None or comp is None or not any(isinstance(n, ast.FunctionDef) and n.name == "build_component" for n in tree.body):
        return source, {}
    skip = _skipped(tree)
    extracted: dict[str, dict] = {}
    defaults: dict[str, Any] = {}
    # un módulo ya normalizado (el hijo de una máquina que ya pasó por aquí): se extiende su `_AUTO`
    prior_node = next((n for n in tree.body if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == "_AUTO" for t in n.targets)), None)
    prior = ast.literal_eval(prior_node.value) if prior_node is not None else {}
    taken = set(prior) | set(comp.get("params") or {})

    class Lift(ast.NodeTransformer):
        def __init__(self, method: str, self_name: str):
            self.method, self.self_name, self.i = method, self_name, 0

        def visit_Constant(self, node):
            v = node.value
            if id(node) in skip or isinstance(v, bool) or not isinstance(v, (int, float)) or _allowed(v):
                return node
            self.i += 1
            name = f"{self.method.strip('_')}_k{self.i}"
            while name in taken:
                self.i += 1
                name = f"{self.method.strip('_')}_k{self.i}"
            taken.add(name)
            extracted[name] = _range_for(v)
            defaults[name] = v
            return ast.copy_location(ast.Attribute(value=ast.Name(id=self.self_name, ctx=ast.Load()), attr=AUTO + name,
                                                   ctx=ast.Load()), node)

    for fn in [b for b in cls.body if isinstance(b, ast.FunctionDef)]:
        if not fn.args.args or any(getattr(d, "id", None) == "staticmethod" for d in fn.decorator_list):
            continue
        Lift(fn.name, fn.args.args[0].arg).visit(fn)
    if not extracted:
        return source, {}
    cls.body[0:0] = [ast.parse(f"{AUTO}{k} = {v!r}").body[0] for k, v in defaults.items()]
    params = dict(comp.get("params") or {})
    params.update(extracted)
    _set_component(tree, {**comp, "params": params})
    if prior_node is not None:
        prior_node.value = ast.parse(repr({**prior, **defaults}), mode="eval").body
        return ast.unparse(tree) + "\n", extracted
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "build_component":
            node.name = "_build_component_llm"
    tail = f"\n\n_MACHINE = {cls.name}\n_AUTO = {defaults!r}\n" + _WRAPPER
    return ast.unparse(tree) + tail, extracted


def inert_params(component: dict, factory: Callable, instances_problems: list[tuple[Any, Any]],
                 signature: Callable[[Any, Any, Any], Any]) -> list[str]:
    params = component.get("params") or {}
    defaults = {p: s["default"] for p, s in params.items() if "default" in s}

    def sigs(values: dict) -> list:
        return [signature(factory(P, **values), P, inst) for inst, P in instances_problems]

    base = sigs(defaults)
    out = []
    for p, spec in params.items():
        if "default" not in spec:
            continue
        alts = [v for v in _alternatives(spec) if v != spec["default"]]
        if not any(sigs({**defaults, p: v}) != base for v in alts):
            out.append(p)
    return out


def normalize_machine_file(path, instances_problems: list[tuple[Any, Any]]) -> list[str]:
    """Normaliza en su lugar el módulo de una máquina generada: extrae los números sueltos como
    parámetros, completa defaults desde la firma de `build_component` y saca de COMPONENT los
    parámetros inertes. Devuelve notas de lo que hizo (para el reporte). Si el módulo no carga,
    no toca nada: lo rechazará la validación."""
    from pathlib import Path

    from .syntactic import load_module

    path = Path(path)
    notes: list[str] = []
    try:
        src, extracted = extract_constants(path.read_text())
    except SyntaxError:
        return notes
    if extracted:
        path.write_text(src)
        notes.append(f"números sueltos extraídos como parámetros: {sorted(extracted)}")
    module, _ = load_module(path)
    component = getattr(module, "COMPONENT", None) if module is not None else None
    factory = getattr(module, "build_component", None) if module is not None else None
    if not isinstance(component, dict) or not callable(factory):
        return notes
    params = dict(component.get("params") or {})
    try:
        sig = inspect.signature(getattr(module, "_build_component_llm", factory)).parameters
    except (TypeError, ValueError):
        sig = {}
    filled = []
    for p, spec in params.items():
        if "default" not in spec and p in sig and sig[p].default is not inspect.Parameter.empty:
            params[p] = {**spec, "default": sig[p].default}
            filled.append(p)
    if filled:
        notes.append(f"defaults tomados de la firma de build_component: {filled}")
    component = {**component, "params": params}
    try:
        inert = inert_params(component, factory, instances_problems, machine_signature)
    except Exception:  # noqa: BLE001 — si construir con otros valores falla, lo reporta params_check
        inert = []
    if inert:
        params = {p: s for p, s in params.items() if p not in inert}
        notes.append(f"parámetros sin efecto sacados de COMPONENT (quedan fijos en su default): {inert}")
    if filled or inert:
        tree = ast.parse(path.read_text())
        _set_component(tree, {**component, "params": params})
        path.write_text(ast.unparse(tree) + "\n")
    return notes


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

    return [(s, repr(a)) for s, a in machine_trace(MachinePolicy(impl, problem), problem.construction_view(inst), max_steps=20_000)]


__all__ = ["loose_constants", "constants_check", "params_check", "machine_signature", "extract_constants",
           "inert_params", "normalize_machine_file"]
