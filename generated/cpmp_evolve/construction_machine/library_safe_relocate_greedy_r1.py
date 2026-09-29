"""Máquina compuesta por la estrategia `library` de evolve: safe_relocate_greedy."""

COMPONENT = {'name': 'library_safe_relocate_greedy', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'p0::safe_relocate_greedy_score_k2': {'type': 'float', 'range': [0.0, 0.2], 'default': 0.1}, 'p0::safe_relocate_greedy_score_k3': {'type': 'float', 'range': [0.0, 0.02], 'default': 0.01}}}

import importlib.util
from pathlib import Path

from core.rules import RuleMachine

_PIECES = [('lib_p0.py', 'p0')]


def _load(fname):
    path = Path(__file__).with_name(fname)
    spec = importlib.util.spec_from_file_location("_piece_" + path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_MODULES = [(_load(f), key) for f, key in _PIECES]


def build_component(problem, **params):
    rules = []
    for k, (mod, key) in enumerate(_MODULES):
        sub = {n.split("::", 1)[1]: v for n, v in params.items() if n.startswith(key + "::")}
        rule = mod.build_component(problem, **sub).rules[0]
        rule.priority = 100 // 2 ** k  # en el orden del compositor
        rules.append(rule)
    return RuleMachine(problem, rules)
