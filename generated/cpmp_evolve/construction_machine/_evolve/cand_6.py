from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from core.machine import FALLBACK
from core.rules import RuleMachine

@dataclass(frozen=True)
class Move:
    so: int
    sd: int
COMPONENT = {'name': 'supporting_safe_move_refined_v6', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}

class SupportingSafeMoveRule:
    name = 'supporting_safe_move'

    def __init__(self, problem, w_bad: float=8.0, w_ub: float=6.0, w_dest_sorted: float=2.5, w_src_sorted: float=1.5, w_gap: float=1.0, w_fill: float=0.75, w_dest_empty: float=4.0, w_src_ub: float=1.5, max_bad_increase: int=1, prefer_safe_only: bool=True):
        self.problem = problem
        self.w_bad = w_bad
        self.w_ub = w_ub
        self.w_dest_sorted = w_dest_sorted
        self.w_src_sorted = w_src_sorted
        self.w_gap = w_gap
        self.w_fill = w_fill
        self.w_dest_empty = w_dest_empty
        self.w_src_ub = w_src_ub
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
        src_ub = partial.ub(so)
        dest_empty = 1 if not partial.stacks[sd] else 0
        fill_after = partial.H - (partial.h(sd) + 1)
        return (bad_delta, ub_delta, dest_empty, 1 - dst_sorted_after, 1 - dst_sorted_before, -src_ub, src_sorted, gap, fill_after, so, sd)

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

class GatedSafePlacementTransitions:

    def __init__(self, bad_limit: int=8, ub_limit: int=4, sorted_stack_limit: int=2, prefer_rule_when_feasible: bool=True):
        self.bad_limit = bad_limit
        self.ub_limit = ub_limit
        self.sorted_stack_limit = sorted_stack_limit
        self.prefer_rule_when_feasible = prefer_rule_when_feasible

    def initial(self, partial):
        return ()

    def _sorted_stacks(self, partial) -> int:
        return sum((1 for i in range(partial.S) if partial.is_sorted_stack(i)))

    def _total_ub(self, partial) -> int:
        return sum((partial.ub(i) for i in range(partial.S)))

    def select(self, partial, memory, rules):
        if not rules.applies(SupportingSafeMoveRule.name):
            return (FALLBACK, memory)
        bad = partial.bad()
        total_ub = self._total_ub(partial)
        sorted_stacks = self._sorted_stacks(partial)
        if self.prefer_rule_when_feasible:
            if bad <= self.bad_limit:
                return (SupportingSafeMoveRule.name, memory)
            if total_ub <= self.ub_limit:
                return (SupportingSafeMoveRule.name, memory)
            if sorted_stacks <= self.sorted_stack_limit:
                return (SupportingSafeMoveRule.name, memory)
            return (FALLBACK, memory)
        if bad <= self.bad_limit and total_ub <= self.ub_limit:
            return (SupportingSafeMoveRule.name, memory)
        if sorted_stacks <= self.sorted_stack_limit:
            return (SupportingSafeMoveRule.name, memory)
        return (FALLBACK, memory)

def _build_component_llm(problem, **params):
    rule = SupportingSafeMoveRule(problem, **params)
    transitions = GatedSafePlacementTransitions()
    return RuleMachine(problem, [rule], transitions)

def _build_component_llm2(problem, **params):
    return _build_component_llm(problem, **params)
_AUTO = {'supporting_safe_move_w_bad': 8.0, 'supporting_safe_move_w_ub': 6.0, 'supporting_safe_move_w_dest_sorted': 2.5, 'supporting_safe_move_w_src_sorted': 1.5, 'supporting_safe_move_w_gap': 1.0, 'supporting_safe_move_w_fill': 0.75, 'supporting_safe_move_w_dest_empty': 4.0, 'supporting_safe_move_w_src_ub': 1.5, 'supporting_safe_move_max_bad_increase': 1, 'supporting_safe_move_prefer_safe_only': True, 'gatedsafeplacementtransitions_bad_limit': 8, 'gatedsafeplacementtransitions_ub_limit': 4, 'gatedsafeplacementtransitions_sorted_stack_limit': 2, 'gatedsafeplacementtransitions_prefer_rule_when_feasible': True}
_AUTO_OWNER = {'supporting_safe_move_w_bad': 'SupportingSafeMoveRule', 'supporting_safe_move_w_ub': 'SupportingSafeMoveRule', 'supporting_safe_move_w_dest_sorted': 'SupportingSafeMoveRule', 'supporting_safe_move_w_src_sorted': 'SupportingSafeMoveRule', 'supporting_safe_move_w_gap': 'SupportingSafeMoveRule', 'supporting_safe_move_w_fill': 'SupportingSafeMoveRule', 'supporting_safe_move_w_dest_empty': 'SupportingSafeMoveRule', 'supporting_safe_move_w_src_ub': 'SupportingSafeMoveRule', 'supporting_safe_move_max_bad_increase': 'SupportingSafeMoveRule', 'supporting_safe_move_prefer_safe_only': 'SupportingSafeMoveRule', 'gatedsafeplacementtransitions_bad_limit': 'GatedSafePlacementTransitions', 'gatedsafeplacementtransitions_ub_limit': 'GatedSafePlacementTransitions', 'gatedsafeplacementtransitions_sorted_stack_limit': 'GatedSafePlacementTransitions', 'gatedsafeplacementtransitions_prefer_rule_when_feasible': 'GatedSafePlacementTransitions'}
_AUTO_ATTR = {'supporting_safe_move_w_bad': 'w_bad', 'supporting_safe_move_w_ub': 'w_ub', 'supporting_safe_move_w_dest_sorted': 'w_dest_sorted', 'supporting_safe_move_w_src_sorted': 'w_src_sorted', 'supporting_safe_move_w_gap': 'w_gap', 'supporting_safe_move_w_fill': 'w_fill', 'supporting_safe_move_w_dest_empty': 'w_dest_empty', 'supporting_safe_move_w_src_ub': 'w_src_ub', 'supporting_safe_move_max_bad_increase': 'max_bad_increase', 'supporting_safe_move_prefer_safe_only': 'prefer_safe_only', 'gatedsafeplacementtransitions_bad_limit': 'bad_limit', 'gatedsafeplacementtransitions_ub_limit': 'ub_limit', 'gatedsafeplacementtransitions_sorted_stack_limit': 'sorted_stack_limit', 'gatedsafeplacementtransitions_prefer_rule_when_feasible': 'prefer_rule_when_feasible'}
_AUTO_CLASSES = {'GatedSafePlacementTransitions': GatedSafePlacementTransitions, 'SupportingSafeMoveRule': SupportingSafeMoveRule}
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
