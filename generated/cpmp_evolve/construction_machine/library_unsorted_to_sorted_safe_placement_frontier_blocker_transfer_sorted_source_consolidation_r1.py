"""Máquina compuesta por la estrategia `library` de evolve: unsorted_to_sorted_safe_placement > frontier_blocker_transfer > sorted_source_consolidation."""
COMPONENT = {'name': 'library_unsorted_to_sorted_safe_placement_frontier_blocker_transfer_sorted_source_consolidation', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'p9::single_bad_count': {'type': 'int', 'range': [1, 3], 'default': 1}, 'p9::min_sorted_prefix': {'type': 'int', 'range': [0, 5], 'default': 1}, 'p9::frontier_max_height': {'type': 'int', 'range': [1, 6], 'default': 2}, 'p9::allow_bad_suffix_receivers': {'type': 'bool', 'default': True}, 'p9::prefer_single_blocker_source_bonus': {'type': 'float', 'range': [0.0, 20.0], 'default': 2.0}, 'p9::prefer_safe_sorted_dest_bonus': {'type': 'float', 'range': [0.0, 20.0], 'default': 3.0}, 'p9::prefer_capped_dest_bonus': {'type': 'float', 'range': [0.0, 20.0], 'default': 1.0}, 'p9::prefer_short_source_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 2.0}, 'p9::prefer_long_dest_prefix_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 1.0}, 'p9::prefer_tighter_fit_weight': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.1}, 'p7::max_source_height': {'type': 'int', 'range': [1, 10], 'default': 3}, 'p7::max_source_bad_suffix': {'type': 'int', 'range': [0, 3], 'default': 1}}}
import importlib.util
from pathlib import Path
from core.rules import RuleMachine
_PIECES = [('lib_p3.py', 'p3'), ('lib_p9.py', 'p9'), ('lib_p7.py', 'p7')]

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
