from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from core.machine import FALLBACK
from core.rules import RuleMachine

@dataclass(frozen=True)
class Move:
    so: int
    sd: int
COMPONENT = {'name': 'supporting_safe_move_refined_v5', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}

class SupportingSafeMoveRule:
    name = 'supporting_safe_move'

    def __init__(self, problem, w_bad: float=8.0, w_ub: float=6.0, w_dest_sorted: float=1.5, w_src_sorted: float=2.5, w_gap: float=1.0, w_fill: float=0.75, max_bad_increase: int=1, prefer_safe_only: bool=True):
        self.problem = problem
        self.w_bad = w_bad
        self.w_ub = w_ub
        self.w_dest_sorted = w_dest_sorted
        self.w_src_sorted = w_src_sorted
        self.w_gap = w_gap
        self.w_fill = w_fill
        self.max_bad_increase = max_bad_increase
        self.prefer_safe_only = prefer_safe_only

    def init(self, partial):
        return ()

    def start(self, partial, memory):
        return memory

    def update(self, partial, memory, action):
        return memory

    def done(self, partial, memory):
        return True

    def _total_ub(self, partial) -> int:
        return sum((partial.ub(i) for i in range(partial.S)))

    def _score(self, partial, so: int, sd: int) -> Tuple:
        trial = partial.copy(track=False)
        trial.move(so, sd)
        base_bad = partial.bad()
        new_bad = trial.bad()
        base_ub = self._total_ub(partial)
        new_ub = self._total_ub(trial)
        bad_delta = new_bad - base_bad
        ub_delta = new_ub - base_ub
        src_sorted = 1 if partial.is_sorted_stack(so) else 0
        dst_sorted_before = 1 if partial.is_sorted_stack(sd) else 0
        dst_sorted_after = 1 if trial.is_sorted_stack(sd) else 0
        moved = partial.g(so)
        dest_top_before = partial.g(sd) if partial.stacks[sd] else partial.G
        gap = max(0, dest_top_before - moved)
        fill_after = partial.H - (partial.h(sd) + 1)
        return (bad_delta, ub_delta, src_sorted, 1 - dst_sorted_after, 1 - dst_sorted_before, gap, fill_after, so, sd)

    def propose(self, partial, memory):
        candidates: List[Tuple[Tuple, int, int]] = []
        safe_candidates: List[Tuple[Tuple, int, int]] = []
        base_bad = partial.bad()
        for so in range(partial.S):
            if not partial.stacks[so]:
                continue
            for sd in range(partial.S):
                if not partial.valid(so, sd):
                    continue
                trial = partial.copy(track=False)
                trial.move(so, sd)
                bad_delta = trial.bad() - base_bad
                score = self._score(partial, so, sd)
                item = (score, so, sd)
                candidates.append(item)
                if bad_delta <= self.max_bad_increase:
                    safe_candidates.append(item)
        if not candidates:
            return []
        if self.prefer_safe_only and safe_candidates:
            safe_candidates.sort(key=lambda x: x[0])
            return [Move(so=so, sd=sd) for _, so, sd in safe_candidates]
        candidates.sort(key=lambda x: x[0])
        return [Move(so=so, sd=sd) for _, so, sd in candidates]

class SafePlacementTransitions:

    def initial(self, partial):
        return ()

    def select(self, partial, memory, rules):
        if rules.applies(SupportingSafeMoveRule.name):
            return (SupportingSafeMoveRule.name, memory)
        return (FALLBACK, memory)

def _build_component_llm(problem, **params):
    rule = SupportingSafeMoveRule(problem, **params)
    transitions = SafePlacementTransitions()
    return RuleMachine(problem, [rule], transitions)

def _build_component_llm2(problem, **params):
    return _build_component_llm(problem, **params)
_AUTO = {'supporting_safe_move_w_bad': 8.0, 'supporting_safe_move_w_ub': 6.0, 'supporting_safe_move_w_dest_sorted': 1.5, 'supporting_safe_move_w_src_sorted': 2.5, 'supporting_safe_move_w_gap': 1.0, 'supporting_safe_move_w_fill': 0.75, 'supporting_safe_move_max_bad_increase': 1, 'supporting_safe_move_prefer_safe_only': True}
_AUTO_OWNER = {'supporting_safe_move_w_bad': 'SupportingSafeMoveRule', 'supporting_safe_move_w_ub': 'SupportingSafeMoveRule', 'supporting_safe_move_w_dest_sorted': 'SupportingSafeMoveRule', 'supporting_safe_move_w_src_sorted': 'SupportingSafeMoveRule', 'supporting_safe_move_w_gap': 'SupportingSafeMoveRule', 'supporting_safe_move_w_fill': 'SupportingSafeMoveRule', 'supporting_safe_move_max_bad_increase': 'SupportingSafeMoveRule', 'supporting_safe_move_prefer_safe_only': 'SupportingSafeMoveRule'}
_AUTO_ATTR = {'supporting_safe_move_w_bad': 'w_bad', 'supporting_safe_move_w_ub': 'w_ub', 'supporting_safe_move_w_dest_sorted': 'w_dest_sorted', 'supporting_safe_move_w_src_sorted': 'w_src_sorted', 'supporting_safe_move_w_gap': 'w_gap', 'supporting_safe_move_w_fill': 'w_fill', 'supporting_safe_move_max_bad_increase': 'max_bad_increase', 'supporting_safe_move_prefer_safe_only': 'prefer_safe_only'}
_AUTO_CLASSES = {'SupportingSafeMoveRule': SupportingSafeMoveRule}
_AUTO_FACTORY = '_build_component_llm2'

def build_component(problem, **params):
    """Envoltura del framework: los números que el LLM dejó sueltos en los métodos son parámetros
    (`_AUTO`, declarados en COMPONENT; `_AUTO_OWNER`: la clase de cada uno). Se fijan en las clases
    mientras se construye (por si un `__init__` los usa) y en cada instancia: la máquina, sus
    reglas y sus transiciones."""
    attrs = globals().get('_AUTO_ATTR', {})
    auto = {k: params.pop(k, v) for k, v in _AUTO.items()}
    lifted = [k for k in auto if k not in attrs]
    saved = {k: getattr(_AUTO_CLASSES[_AUTO_OWNER[k]], '_auto_' + k) for k in lifted}
    for k in lifted:
        setattr(_AUTO_CLASSES[_AUTO_OWNER[k]], '_auto_' + k, auto[k])
    try:
        obj = _build_component_llm2(problem, **params)
    finally:
        for k, v in saved.items():
            setattr(_AUTO_CLASSES[_AUTO_OWNER[k]], '_auto_' + k, v)
    parts = [obj, getattr(obj, 'transitions', None), *list(getattr(obj, 'rules', None) or [])]
    for part in parts:
        for k, v in auto.items():
            if part is not None and isinstance(part, _AUTO_CLASSES[_AUTO_OWNER[k]]):
                setattr(part, attrs.get(k, '_auto_' + k), v)
    return obj
