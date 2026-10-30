"""Compila e importa un módulo nativo (C++ con pybind11) de un pack.

    mod = load_module("hsf_jobshop", "examples/jobshop/native/jobshop_py.cpp")

El .so queda en `native/_build/`, con un nombre que depende del código (el .cpp y los headers de
su directorio y de `native/include`) y de las opciones: si nada cambió, no se recompila. Un error
de compilación es un `NativeBuildError` con la salida del compilador (para el validador: un
componente C++ que no compila se rechaza con ese mensaje, como un SyntaxError en Python).

`sanitize=True` agrega AddressSanitizer y UBSan (para validar código generado; más lento). Un
módulo así solo se puede importar en un proceso con la biblioteca de ASan precargada
(`LD_PRELOAD`), así que se usa desde un subproceso.
"""

from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import subprocess
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INCLUDE = ROOT / "include"
BUILD = ROOT / "_build"
FLAGS = ["-O2", "-std=c++17", "-shared", "-fPIC", "-fvisibility=hidden", "-Wall"]
SANITIZE = ["-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"]


class NativeBuildError(RuntimeError):
    pass


def _includes() -> list[str]:
    import pybind11

    return [str(INCLUDE), pybind11.get_include(), sysconfig.get_paths()["include"]]


def _digest(source: Path, flags: list[str], include_dirs: list[Path]) -> str:
    h = hashlib.sha256(" ".join(flags).encode())
    headers = [*source.parent.glob("*.hpp"), *INCLUDE.rglob("*.hpp")] + [p for d in include_dirs for p in d.glob("*.hpp")]
    for p in sorted(set([source, *headers])):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def build(name: str, source: str | Path, sanitize: bool = False, extra_flags: list[str] | None = None,
          timeout: float = 300.0, include_dirs: list[str | Path] | None = None) -> Path:
    source = Path(source).resolve()
    incs = [Path(d).resolve() for d in include_dirs or []]
    flags = FLAGS + (SANITIZE if sanitize else []) + list(extra_flags or [])
    suffix = sysconfig.get_config_var("EXT_SUFFIX") or ".so"
    out = BUILD / f"{name}-{_digest(source, flags, incs)}{'-asan' if sanitize else ''}" / f"{name}{suffix}"
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["g++", *flags, *(f"-I{d}" for d in _includes()), *(f"-I{d}" for d in incs), f"-I{source.parent}", str(source),
           "-o", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise NativeBuildError(f"no compila {source.name}:\n{proc.stderr[-6000:]}")
    return out


def load_module(name: str, source: str | Path, **kw):
    """Compila (si hace falta) e importa el módulo `name`."""
    if name in sys.modules:
        return sys.modules[name]
    return import_path(name, build(name, source, **kw))


def import_path(name: str, path: str | Path):
    """Importa un módulo de extensión ya compilado."""
    if name in sys.modules:
        return sys.modules[name]
    path = str(path)
    loader = importlib.machinery.ExtensionFileLoader(name, path)
    spec = importlib.util.spec_from_file_location(name, path, loader=loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    sys.modules[name] = mod
    return mod


__all__ = ["NativeBuildError", "build", "import_path", "load_module"]
