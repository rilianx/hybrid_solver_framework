from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from core.machine import FALLBACK
from core.rules import RuleMachine

@dataclass(frozen=True)
class Move:
    so: int
    sd: int
COMPONENT = {'name': 'supporting_safe_move_refined_v5_8', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'supporting_safe_move_score_k3': {'type': 'float', 'range': [0.0, 0.002], 'default': 0.001}}}

class SupportingSafeMoveRule:
    _auto_supporting_safe_move_score_k1 = 0.25
    _auto_supporting_safe_move_score_k2 = 0.15
    _auto_supporting_safe_move_score_k3 = 0.001
    name = 'supporting_safe_move'

    def __init__(self, problem, w_bad: float=7.5, w_ub: float=5.5, w_unlock: float=4.0, w_dest_room: float=1.5, w_dest_sorted: float=1.0, w_src_sorted: float=1.5, w_gap: float=0.6, w_fill: float=0.4, prefer_safe_only: bool=False, max_bad_increase: int=1):
        self.problem = problem
        self.w_bad = w_bad
        self.w_ub = w_ub
        self.w_unlock = w_unlock
        self.w_dest_room = w_dest_room
        self.w_dest_sorted = w_dest_sorted
        self.w_src_sorted = w_src_sorted
        self.w_gap = w_gap
        self.w_fill = w_fill
        self.prefer_safe_only = prefer_safe_only
        self.max_bad_increase = max_bad_increase

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

    def _score(self, partial, so: int, sd: int) -> float:
        c = partial.g(so)
        trial = partial.copy(track=False)
        trial.move(so, sd)
        base_bad = partial.bad()
        new_bad = trial.bad()
        base_ub = self._total_ub(partial)
        new_ub = self._total_ub(trial)
        src_sorted_before = partial.is_sorted_stack(so)
        src_sorted_after = trial.is_sorted_stack(so)
        dst_sorted_before = partial.is_sorted_stack(sd)
        dst_sorted_after = trial.is_sorted_stack(sd)
        src_ub_before = partial.ub(so)
        src_ub_after = trial.ub(so)
        dst_ub_before = partial.ub(sd)
        dst_ub_after = trial.ub(sd)
        dst_height_after = trial.h(sd)
        dest_top_before = partial.g(sd)
        gap = max(0, dest_top_before - c)
        fill = partial.H - dst_height_after
        unlock_gain = src_ub_before - src_ub_after + (dst_ub_before - dst_ub_after)
        room_gain = partial.e(sd)
        score = self.w_bad * new_bad + self.w_ub * new_ub - self.w_unlock * unlock_gain - self.w_dest_room * room_gain - self.w_dest_sorted * (1.0 if dst_sorted_after else 0.0) - self.w_src_sorted * (1.0 if src_sorted_after else 0.0) + self.w_gap * gap + self.w_fill * fill
        if dst_sorted_before and (not dst_sorted_after):
            score += self._auto_supporting_safe_move_score_k1
        if src_sorted_before and (not src_sorted_after):
            score += self._auto_supporting_safe_move_score_k2
        score += self._auto_supporting_safe_move_score_k3 * so + 0.0001 * sd
        score += 1e-05 * (base_bad - new_bad) + 1e-06 * (base_ub - new_ub)
        return score

    def propose(self, partial, memory):
        candidates: List[Tuple[float, int, int]] = []
        safe_candidates: List[Tuple[float, int, int]] = []
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
            safe_candidates.sort(key=lambda x: (x[0], x[1], x[2]))
            return [Move(so=so, sd=sd) for _, so, sd in safe_candidates]
        candidates.sort(key=lambda x: (x[0], x[1], x[2]))
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
_AUTO = {'supporting_safe_move_w_bad': 7.5, 'supporting_safe_move_w_ub': 5.5, 'supporting_safe_move_w_unlock': 4.0, 'supporting_safe_move_w_dest_room': 1.5, 'supporting_safe_move_w_dest_sorted': 1.0, 'supporting_safe_move_w_src_sorted': 1.5, 'supporting_safe_move_w_gap': 0.6, 'supporting_safe_move_w_fill': 0.4, 'supporting_safe_move_prefer_safe_only': False, 'supporting_safe_move_max_bad_increase': 1, 'supporting_safe_move_score_k1': 0.25, 'supporting_safe_move_score_k2': 0.15, 'supporting_safe_move_score_k3': 0.001}
_AUTO_OWNER = {'supporting_safe_move_w_bad': 'SupportingSafeMoveRule', 'supporting_safe_move_w_ub': 'SupportingSafeMoveRule', 'supporting_safe_move_w_unlock': 'SupportingSafeMoveRule', 'supporting_safe_move_w_dest_room': 'SupportingSafeMoveRule', 'supporting_safe_move_w_dest_sorted': 'SupportingSafeMoveRule', 'supporting_safe_move_w_src_sorted': 'SupportingSafeMoveRule', 'supporting_safe_move_w_gap': 'SupportingSafeMoveRule', 'supporting_safe_move_w_fill': 'SupportingSafeMoveRule', 'supporting_safe_move_prefer_safe_only': 'SupportingSafeMoveRule', 'supporting_safe_move_max_bad_increase': 'SupportingSafeMoveRule', 'supporting_safe_move_score_k1': 'SupportingSafeMoveRule', 'supporting_safe_move_score_k2': 'SupportingSafeMoveRule', 'supporting_safe_move_score_k3': 'SupportingSafeMoveRule'}
_AUTO_ATTR = {'supporting_safe_move_w_bad': 'w_bad', 'supporting_safe_move_w_ub': 'w_ub', 'supporting_safe_move_w_unlock': 'w_unlock', 'supporting_safe_move_w_dest_room': 'w_dest_room', 'supporting_safe_move_w_dest_sorted': 'w_dest_sorted', 'supporting_safe_move_w_src_sorted': 'w_src_sorted', 'supporting_safe_move_w_gap': 'w_gap', 'supporting_safe_move_w_fill': 'w_fill', 'supporting_safe_move_prefer_safe_only': 'prefer_safe_only', 'supporting_safe_move_max_bad_increase': 'max_bad_increase'}
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
