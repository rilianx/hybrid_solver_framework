"""Máquina compuesta por la estrategia `library` de evolve: unsorted_to_sorted_safe_placement > frontier_blocker_transfer > sorted_source_consolidation."""
COMPONENT = {'name': 'library_unsorted_to_sorted_safe_placement_frontier_blocker_transfer_sorted_source_consolidation', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'p2::min_sorted_prefix': {'type': 'int', 'range': [0, 5], 'default': 1}, 'p2::prefer_tighter_fit_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.1}, 'p7::min_source_height': {'type': 'int', 'range': [1, 10], 'default': 1}, 'p7::max_source_height': {'type': 'int', 'range': [1, 10], 'default': 3}, 'p7::max_source_bad_suffix': {'type': 'int', 'range': [0, 3], 'default': 1}, 'p7::min_exposed_sorted_prefix': {'type': 'int', 'range': [0, 10], 'default': 1}, 'p7::allow_unsorted_receivers': {'type': 'bool', 'default': True}, 'p7::allow_sorted_receivers': {'type': 'bool', 'default': True}, 'p7::prefer_safe_sorted_placement': {'type': 'bool', 'default': True}, 'p7::prefer_near_sorted_peel': {'type': 'bool', 'default': True}, 'p7::prefer_taller_receivers': {'type': 'bool', 'default': True}}}
import importlib.util
from pathlib import Path
from core.rules import RuleMachine
_PIECES = [('lib_p3.py', 'p3'), ('lib_p2.py', 'p2'), ('lib_p7.py', 'p7')]

def _load(fname):
    path = Path(__file__).with_name(fname)
    spec = importlib.util.spec_from_file_location('_piece_' + path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
_MODULES = [(_load(f), key) for f, key in _PIECES]

def build_component(problem, **params):
    rules = []
    for k, (mod, key) in enumerate(_MODULES):
        sub = {n.split('::', 1)[1]: v for n, v in params.items() if n.startswith(key + '::')}
        rule = mod.build_component(problem, **sub).rules[0]
        rule.priority = 100 // 2 ** k
        rules.append(rule)
    return RuleMachine(problem, rules)
