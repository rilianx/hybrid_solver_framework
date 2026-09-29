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
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and (t.id in ("COMPONENT", "_AUTO", "_AUTO_OWNER", "_AUTO_ATTR") or t.id.startswith(AUTO))
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


_WRAPPER_MULTI = '''
def build_component(problem, **params):
    """Envoltura del framework: los números que el LLM dejó sueltos en los métodos son parámetros
    (`_AUTO`, declarados en COMPONENT; `_AUTO_OWNER`: la clase de cada uno). Se fijan en las clases
    mientras se construye (por si un `__init__` los usa) y en cada instancia: la máquina, sus
    reglas y sus transiciones."""
    attrs = globals().get("_AUTO_ATTR", {})  # parámetro -> atributo de la instancia (los defaults de un __init__)
    auto = {k: params.pop(k, v) for k, v in _AUTO.items()}
    lifted = [k for k in auto if k not in attrs]
    saved = {k: getattr(_AUTO_CLASSES[_AUTO_OWNER[k]], "_auto_" + k) for k in lifted}
    for k in lifted:
        setattr(_AUTO_CLASSES[_AUTO_OWNER[k]], "_auto_" + k, auto[k])
    try:
        obj = _build_component_llm(problem, **params)
    finally:
        for k, v in saved.items():
            setattr(_AUTO_CLASSES[_AUTO_OWNER[k]], "_auto_" + k, v)
    parts = [obj, getattr(obj, "transitions", None), *list(getattr(obj, "rules", None) or [])]
    for part in parts:
        for k, v in auto.items():
            if part is not None and isinstance(part, _AUTO_CLASSES[_AUTO_OWNER[k]]):
                setattr(part, attrs.get(k, "_auto_" + k), v)
    return obj
'''


def _assign(tree, name: str):
    return next((n for n in tree.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)), None)


def _target_classes(tree) -> list[ast.ClassDef]:
    """Las clases cuyos números son parámetros: reglas (`propose`), transiciones (`select`) y
    máquinas (atributo `states`)."""
    out = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        methods = {b.name for b in node.body if isinstance(b, ast.FunctionDef)}
        has_states = any(isinstance(b, (ast.Assign, ast.AnnAssign)) and any(
            getattr(t, "id", None) == "states" for t in (b.targets if isinstance(b, ast.Assign) else [b.target])) for b in node.body)
        if methods & {"propose", "select"} or has_states:
            out.append(node)
    return out


def _prefix(cls: ast.ClassDef) -> str:
    """Prefijo de los nombres de parámetro: el `name` de una regla; nada para una máquina; si no, la clase."""
    for b in cls.body:
        if isinstance(b, ast.Assign) and any(getattr(t, "id", None) == "name" for t in b.targets) \
                and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
            return b.value.value + "_"
    if any(isinstance(b, (ast.Assign, ast.AnnAssign)) and any(
            getattr(t, "id", None) == "states" for t in (b.targets if isinstance(b, ast.Assign) else [b.target])) for b in cls.body):
        return ""
    return cls.name.lower() + "_"


def _init_defaults(cls: ast.ClassDef, prefix: str, taken: set) -> list[tuple[str, dict, str]]:
    """Los defaults numéricos (o bool) de un `__init__` que se guardan tal cual en un atributo
    (`def __init__(self, ..., w_bad=8.0): self.w_bad = w_bad`): son parámetros escondidos, porque
    build_component no los pasa (corrida 72: ocho pesos así, fuera del tuner). (parámetro,
    especificación, atributo)."""
    init = next((b for b in cls.body if isinstance(b, ast.FunctionDef) and b.name == "__init__"), None)
    if init is None or not init.args.args:
        return []
    self_name = init.args.args[0].arg
    stored = {t.attr for n in ast.walk(init) if isinstance(n, ast.Assign) for t in n.targets
              if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == self_name
              and isinstance(n.value, ast.Name) and n.value.id == t.attr}
    args = init.args.args[1:]
    defaults = init.args.defaults
    out = []
    for arg, d in zip(args[len(args) - len(defaults):], defaults):
        if arg.arg not in stored or not isinstance(d, ast.Constant):
            continue
        v = d.value
        name = f"{prefix}{arg.arg}"
        if name in taken or arg.arg in taken:  # ya es un parámetro (build_component lo pasa)
            continue
        if isinstance(v, bool):
            out.append((name, {"type": "bool", "default": v}, arg.arg))
        elif isinstance(v, (int, float)) and v != 0:
            out.append((name, _range_for(v), arg.arg))
    return out


def extract_constants(source: str) -> tuple[str, dict]:
    """(fuente nueva, {parámetro: especificación}): cada número suelto dentro de un método de una
    regla, de las transiciones o de la máquina pasa a ser `self._auto_<prefijo><método>_k<i>` y un
    parámetro de COMPONENT. Un módulo ya normalizado se extiende."""
    tree = ast.parse(source)
    comp = _component_of(tree)
    if comp is None or not any(isinstance(n, ast.FunctionDef) and n.name in ("build_component", "_build_component_llm")
                               for n in tree.body):
        return source, {}
    legacy = _assign(tree, "_MACHINE") is not None  # normalizado antes de las máquinas de reglas: una sola clase
    classes = [_machine_class(tree)] if legacy else _target_classes(tree)
    classes = [c for c in classes if c is not None]
    if not classes:
        return source, {}
    skip = _skipped(tree)
    prior_node, owner_node = _assign(tree, "_AUTO"), _assign(tree, "_AUTO_OWNER")
    prior = ast.literal_eval(prior_node.value) if prior_node is not None else {}
    owners = ast.literal_eval(owner_node.value) if owner_node is not None else {}
    taken = set(prior) | set(comp.get("params") or {})
    extracted: dict[str, dict] = {}
    defaults: dict[str, Any] = {}
    new_owner: dict[str, str] = {}

    class Lift(ast.NodeTransformer):
        def __init__(self, stem: str, self_name: str, cls_name: str):
            self.stem, self.self_name, self.cls_name, self.i = stem, self_name, cls_name, 0

        def visit_Constant(self, node):
            v = node.value
            if id(node) in skip or isinstance(v, bool) or not isinstance(v, (int, float)) or _allowed(v):
                return node
            self.i += 1
            name = f"{self.stem}_k{self.i}"
            while name in taken:
                self.i += 1
                name = f"{self.stem}_k{self.i}"
            taken.add(name)
            extracted[name], defaults[name], new_owner[name] = _range_for(v), v, self.cls_name
            return ast.copy_location(ast.Attribute(value=ast.Name(id=self.self_name, ctx=ast.Load()), attr=AUTO + name,
                                                   ctx=ast.Load()), node)

    attr_of: dict[str, str] = {}  # parámetros que son defaults de un __init__: parámetro -> atributo
    for cls in classes:
        pre = "" if legacy else _prefix(cls)
        before = len(defaults)
        for fn in [b for b in cls.body if isinstance(b, ast.FunctionDef)]:
            if not fn.args.args or any(getattr(d, "id", None) == "staticmethod" for d in fn.decorator_list):
                continue
            Lift(pre + fn.name.strip("_"), fn.args.args[0].arg, cls.name).visit(fn)
        mine = [k for k in list(defaults)[before:]]
        cls.body[0:0] = [ast.parse(f"{AUTO}{k} = {defaults[k]!r}").body[0] for k in mine]
        if not legacy:
            for k, spec, attr in _init_defaults(cls, pre, taken):
                taken.add(k)
                extracted[k], defaults[k], new_owner[k], attr_of[k] = spec, spec["default"], cls.name, attr
    if not extracted:
        return source, {}
    params = dict(comp.get("params") or {})
    params.update(extracted)
    _set_component(tree, {**comp, "params": params})
    if prior_node is not None:  # ya normalizado: se extienden sus tablas
        prior_node.value = ast.parse(repr({**prior, **defaults}), mode="eval").body
        attr_node = _assign(tree, "_AUTO_ATTR")
        if attr_node is not None:
            attr_node.value = ast.parse(repr({**ast.literal_eval(attr_node.value), **attr_of}), mode="eval").body
        elif attr_of:  # normalizado antes de extraer los defaults de __init__
            tree.body.insert(tree.body.index(prior_node) + 1, ast.parse(f"_AUTO_ATTR = {attr_of!r}").body[0])
        if not legacy:
            fac = _assign(tree, "_AUTO_FACTORY")
            target = ast.literal_eval(fac.value) if fac is not None else "_build_component_llm"
            wrapper = ast.parse(_WRAPPER_MULTI.replace("_build_component_llm(problem", target + "(problem")).body[0]
            for i, node in enumerate(tree.body):  # la envoltura actual (una anterior no conocía _AUTO_ATTR)
                if isinstance(node, ast.FunctionDef) and node.name == "build_component":
                    tree.body[i] = wrapper
            all_owner = {**owners, **new_owner}
            owner_node.value = ast.parse(repr(all_owner), mode="eval").body
            classes_node = _assign(tree, "_AUTO_CLASSES")
            names = sorted(set(all_owner.values()))
            classes_node.value = ast.parse("{" + ", ".join(f"{n!r}: {n}" for n in names) + "}", mode="eval").body
        return ast.unparse(tree) + "\n", extracted
    # corrida 72: el módulo ya tenía su propio `_build_component_llm` (y build_component lo
    # llamaba); renombrar build_component a ese nombre lo volvía recursivo. Se usa uno libre.
    used = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))} | \
        {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    target, i = "_build_component_llm", 1
    while target in used:
        i += 1
        target = f"_build_component_llm{i}"
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "build_component":
            node.name = target
    names = sorted(set(new_owner.values()))
    tail = (f"\n\n_AUTO = {defaults!r}\n_AUTO_OWNER = {new_owner!r}\n_AUTO_ATTR = {attr_of!r}\n"
            f"_AUTO_CLASSES = {{{', '.join(f'{n!r}: {n}' for n in names)}}}\n_AUTO_FACTORY = {target!r}\n"
            + _WRAPPER_MULTI.replace("_build_component_llm(problem", target + "(problem"))
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
        sig = inspect.signature(getattr(module, getattr(module, "_AUTO_FACTORY", "_build_component_llm"), factory)).parameters
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
