"""Máquina compuesta por la estrategia `library` de evolve: move_good_top_to_bad_stack > move_bad_top_to_empty_stack > repair_bad_top_move."""

COMPONENT = {'name': 'library_move_good_top_to_bad_stack_move_bad_top_to_empty_stack_repair_bad_top_move', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'p4::prefer_more_bad_destinations': {'type': 'bool', 'default': True}, 'p7::repair_bad_top_move_allowed_k2': {'type': 'float', 'range': [0.0, 0.002], 'default': 0.001}}}

import importlib.util
from pathlib import Path

from core.rules import RuleMachine

_PIECES = [('lib_p4.py', 'p4'), ('lib_p8.py', 'p8'), ('lib_p7.py', 'p7')]


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
