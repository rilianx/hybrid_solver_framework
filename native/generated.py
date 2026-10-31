"""Componentes C++ escritos por el LLM: leerlos de la respuesta, compilarlos junto al modelo nativo del
problema y envolverlos con la interfaz de los slots de Python (para el validador y el tuner).

Un componente generado es un bloque ```cpp``` con una línea de metadatos y una fábrica:

    // COMPONENT: {"name": "swap_x", "slot": "neighborhood", "params": {}}
    struct SwapX : hsf::Neighborhood<JobShop> { ... };
    std::unique_ptr<hsf::Neighborhood<JobShop>> make_component(const JobShop& model, const hsf::Config& params) { ... }

Cada uno se compila dentro de su propio espacio de nombres (`hsf_gen_<nombre>`), así dos componentes pueden
usar los mismos nombres de clases. El módulo de extensión que resulta tiene el catálogo con las partidas
de referencia (`trivial`, `random`) y los componentes, los bindings del modelo (`bind_problem` del pack) y
`solve`. Su nombre depende del código, así que módulos distintos conviven en un proceso.

Lo que el pack aporta (`GENERATION` en su módulo nativo, p.ej. `examples/jobshop/native_parts.py`): el
directorio de sus headers, el header del modelo (lo que ve el LLM), el de los bindings, el tipo del modelo
y el módulo Python con la vista MIP.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from random import Random
from types import SimpleNamespace
from typing import Any

from .build import BUILD, build, import_path

SLOT_BASE = {"constructor": "Constructor", "greedy_score": "GreedyScore", "neighborhood": "Neighborhood",
             "perturbation": "Perturbation", "relink": "Relink"}
CATALOG_FIELD = {"constructor": "constructors", "greedy_score": "scores", "neighborhood": "neighborhoods",
                 "perturbation": "perturbations", "relink": "relinks"}
STD_HEADERS = ["algorithm", "array", "cmath", "cstdint", "deque", "functional", "limits", "map", "memory", "numeric",
               "queue", "random", "set", "unordered_map", "unordered_set", "utility", "vector"]
DEBUG_FLAGS = ["-D_GLIBCXX_ASSERTIONS"]  # índices fuera de rango abortan con mensaje en vez de corromper memoria

_BLOCK = re.compile(r"```(?:cpp|c\+\+|cc|hpp)\s*\n(.*?)```", re.DOTALL)
_META = re.compile(r"//\s*COMPONENT:\s*(\{.*\})")
_SAFE = re.compile(r"[^a-zA-Z0-9_]+")


@dataclass
class NativeComponent:
    name: str
    slot: str
    source: str
    component: dict[str, Any] = field(default_factory=dict)  # name, slot, compatible_skeletons, params
    path: Path | None = None


class ParseError(ValueError):
    pass


def parse_component(source: str) -> NativeComponent:
    m = _META.search(source)
    if not m:
        raise ParseError("falta la línea `// COMPONENT: {\"name\": ..., \"slot\": ..., \"params\": {...}}`")
    try:
        meta = json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        raise ParseError(f"la línea COMPONENT no es JSON válido: {exc}") from exc
    name, slot = meta.get("name"), meta.get("slot")
    if not name or not re.fullmatch(r"[a-z][a-z0-9_]*", str(name)):
        raise ParseError(f"COMPONENT['name'] debe ser snake_case: {name!r}")
    if slot not in SLOT_BASE:
        raise ParseError(f"COMPONENT['slot'] debe ser uno de {sorted(SLOT_BASE)}: {slot!r}")
    if "make_component" not in source:
        raise ParseError("falta la fábrica `make_component(const <Modelo>& model, const hsf::Config& params)`")
    meta.setdefault("params", {})
    return NativeComponent(name=name, slot=slot, source=source, component=meta)


def parse_response(text: str) -> tuple[list[NativeComponent], list[str]]:
    """(componentes, errores de los bloques que no se pudieron leer)."""
    out, errors = [], []
    for block in _BLOCK.findall(text):
        try:
            out.append(parse_component(block.strip("\n") + "\n"))
        except ParseError as exc:
            errors.append(str(exc))
    return out, errors


def _body(source: str) -> str:
    """El código sin `#include` ni `#pragma once` (los headers estándar los incluye el módulo)."""
    return "\n".join(ln for ln in source.splitlines() if not re.match(r"\s*#\s*(include|pragma\s+once)\b", ln))


def module_source(gen: dict, components: list[NativeComponent], module_name: str) -> str:
    M = gen["model_type"]
    lines = [f"// generado por native/generated.py: {', '.join(c.name for c in components) or '(sin componentes)'}"]
    lines += [f"#include <{h}>" for h in STD_HEADERS]
    lines += [f'#include "{gen["bindings_header"]}"', ""]
    for c in components:
        lines += [f"namespace hsf_gen_{c.name} {{", f"using namespace {gen['namespace']};",
                  "using hsf::Move;", "using hsf::Rng;", "using hsf::Config;", "", f"#line 1 \"{c.name}.hpp\"",
                  _body(c.source), f"}}  // namespace hsf_gen_{c.name}", ""]
    lines += [f"static hsf::Catalog<{M}> make_catalog() {{", f"    hsf::Catalog<{M}> c;", "    hsf::add_base_constructors(c);"]
    for c in components:
        lines.append(f'    c.{CATALOG_FIELD[c.slot]}["{c.name}"] = [](const {M}& m, const hsf::Config& p) '
                     f"{{ return hsf_gen_{c.name}::make_component(m, p); }};")
    lines += ["    return c;", "}", f"static const hsf::Catalog<{M}> CATALOG = make_catalog();", "",
              f"PYBIND11_MODULE({module_name}, mod) {{",
              f"    hsf::bind_model<{M}>(mod, &CATALOG, {gen['sol_to_py']}, {gen['sol_from_py']});",
              f"    {gen['bind_problem']}(mod);", "}", ""]
    return "\n".join(lines)


def build_components(gen: dict, components: list[NativeComponent], debug: bool = False, timeout: float = 600.0):
    """Compila el módulo con estos componentes; (ruta del .so, nombre del módulo)."""
    h = hashlib.sha256(json.dumps([[c.name, c.slot, c.source] for c in components]).encode() + bytes(debug))
    name = f"hsf_gen_{h.hexdigest()[:12]}"
    src_dir = BUILD / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    src = src_dir / f"{name}.cpp"
    src.write_text(module_source(gen, components, name))
    path = build(name, src, extra_flags=DEBUG_FLAGS if debug else None, include_dirs=[gen["dir"]], timeout=timeout)
    return path, name


# ------------------------------------------------------------------ del lado de Python
class ModelCache:
    def __init__(self, native):
        self.native, self._models = native, {}

    def __call__(self, inst):
        m = self._models.get(inst)
        if m is None:
            if len(self._models) > 256:
                self._models.clear()
            m = self._models[inst] = self.native.parse(inst.to_text())
        return m


def parts_for(native, mip_parts, model_of=None) -> SimpleNamespace:
    """Las piezas de un modelo nativo (`core.model_parts`): vista heurística y constructiva en C++, vista MIP
    de Python (`mip_parts`)."""
    model_of = model_of or ModelCache(native)
    seed = lambda rng: rng.getrandbits(63)  # noqa: E731
    ns = SimpleNamespace(
        native=native, model=model_of,
        canonical=mip_parts.canonical, from_answer=mip_parts.from_answer,
        trivial_solution=lambda inst: native.trivial_solution(model_of(inst)),
        random_solution=lambda inst, rng: native.random_solution(model_of(inst), seed(rng)),
        violations=lambda inst, sol: native.violations(model_of(inst), sol),
        cost_terms=lambda inst, sol: native.cost_terms(model_of(inst), sol),
        empty_partial=lambda inst: native.empty_partial(model_of(inst)),
        candidates=lambda inst, p: native.candidates(model_of(inst), p),
        apply_action=lambda inst, p, a: native.apply_action(model_of(inst), p, a),
        is_complete=lambda inst, p: native.is_complete(model_of(inst), p),
        to_solution=lambda inst, p: native.to_solution(model_of(inst), p),
        complete_partial=lambda inst, p, rng: native.complete_partial(model_of(inst), p, seed(rng)),
    )
    for name in ("variables", "structural_variables", "to_assignment", "aux_values", "from_assignment",
                 "constraint_families", "objective_terms", "variable_groups"):
        setattr(ns, name, getattr(mip_parts, name))
    return ns


class _Wrapper:
    def __init__(self, native, model_of, problem, name, params):
        self.native, self.inst = native, problem.inst
        self.h = self._make(native, model_of(problem.inst), name, dict(params))


class NativeConstructor(_Wrapper):
    _make = staticmethod(lambda nat, m, name, p: nat.make_constructor(m, name, p))

    def build(self, inst, rng: Random):
        return self.h.build(rng.getrandbits(63))


class NativeNeighborhood(_Wrapper):
    _make = staticmethod(lambda nat, m, name, p: nat.make_neighborhood(m, name, p))

    def __init__(self, *a):
        super().__init__(*a)
        if self.h.has_estimate():
            self.estimate = self.h.estimate

    def moves(self, sol):
        return self.h.moves(sol)

    def apply(self, sol, m):
        return self.h.apply(sol, m)

    def delta(self, sol, m):
        return self.h.delta(sol, m)


class NativePerturbation(_Wrapper):
    _make = staticmethod(lambda nat, m, name, p: nat.make_perturbation(m, name, p))

    def perturb(self, sol, strength, rng: Random):
        return self.h.perturb(sol, float(strength), rng.getrandbits(63))


class NativeScore(_Wrapper):
    _make = staticmethod(lambda nat, m, name, p: nat.make_score(m, name, p))

    def score(self, partial, action) -> float:
        return self.h.score(partial, action)


class NativeRelink(_Wrapper):
    _make = staticmethod(lambda nat, m, name, p: nat.make_relink(m, name, p))

    def distance(self, a, b) -> int:
        return self.h.distance(a, b)

    def step(self, cur, guide, rng: Random):
        return self.h.step(cur, guide, rng.getrandbits(63))


WRAPPERS = {"constructor": NativeConstructor, "neighborhood": NativeNeighborhood, "perturbation": NativePerturbation,
            "greedy_score": NativeScore, "relink": NativeRelink}


def factory(native, model_of, slot: str, name: str):
    """`build_component(problem, **params)` de un componente nativo."""
    cls = WRAPPERS[slot]
    return lambda problem, **params: cls(native, model_of, problem, name, params)


__all__ = ["CATALOG_FIELD", "NativeComponent", "ParseError", "SLOT_BASE", "build_components", "factory",
           "module_source", "parse_component", "parse_response", "parts_for"]


def load(path: str | Path, name: str):
    """Importa un módulo compilado por `build_components`."""
    return import_path(name, path)
