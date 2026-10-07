"""Máquina compuesta por la estrategia `library` de evolve: buffer_aware_bad_top_placement > large_bad_top_gap > capped_misordered_source."""
COMPONENT = {'name': 'library_buffer_aware_bad_top_placement_large_bad_top_gap_capped_misordered_source', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'p8::prefer_taller_support_for_compatible': {'type': 'bool', 'default': True}, 'p8::prefer_buffer_for_capped_misordered': {'type': 'bool', 'default': True}, 'p8::min_cover_gap_for_buffer_preference': {'type': 'int', 'range': [0, 100], 'default': 2}, 'p8::prefer_smaller_incompatible_gap': {'type': 'bool', 'default': True}, 'p0::min_gap': {'type': 'int', 'range': [1, 100], 'default': 6}, 'p1::min_cover_gap': {'type': 'int', 'range': [0, 1000000], 'default': 0}, 'p1::min_compatible_dests': {'type': 'int', 'range': [1, 1000], 'default': 1}}}
import importlib.util
from pathlib import Path
from core.parts import assemble
_PIECES = [('lib_p8.py', 'p8'), ('lib_p0.py', 'p0'), ('lib_p1.py', 'p1')]

def _load(fname):
    path = Path(__file__).with_name(fname)
    spec = importlib.util.spec_from_file_location('_piece_' + path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
_MODULES = [(_load(f), key) for f, key in _PIECES]

def build_component(problem, **params):
    machines = []
    for mod, key in _MODULES:
        sub = {n.split('::', 1)[1]: v for n, v in params.items() if n.startswith(key + '::')}
        machines.append(mod.build_component(problem, **sub))
    return assemble(problem, machines, [100 // 2 ** k for k in range(len(machines))])
