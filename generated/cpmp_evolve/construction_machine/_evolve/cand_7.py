from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from core.machine import FALLBACK
from core.rules import RuleMachine

@dataclass(frozen=True)
class Move:
    so: int
    sd: int
COMPONENT = {'name': 'supporting_safe_move_refined_v9_source_pressure', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'supporting_safe_move_w_ub': {'type': 'float', 'range': [0.0, 20.0], 'default': 6.0}, 'supporting_safe_move_w_gap': {'type': 'float', 'range': [0.0, 10.0], 'default': 1.0}, 'supporting_safe_move_w_fill': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.75}}}

class SupportingSafeMoveRule:
    name = 'supporting_safe_move'

    def __init__(self, problem, supporting_safe_move_w_bad: float=8.0, supporting_safe_move_w_ub: float=6.0, supporting_safe_move_w_dest_sorted: float=1.5, supporting_safe_move_w_src_sorted: float=2.5, supporting_safe_move_w_gap: float=1.0, supporting_safe_move_w_fill: float=0.75, supporting_safe_move_w_src_ub: float=2.0, supporting_safe_move_w_src_bad: float=1.5, supporting_safe_move_w_dest_fill: float=0.5, supporting_safe_move_max_bad_increase: int=1, supporting_safe_move_prefer_safe_only: bool=True):
        self.problem = problem
        self.w_bad = supporting_safe_move_w_bad
        self.w_ub = supporting_safe_move_w_ub
        self.w_dest_sorted = supporting_safe_move_w_dest_sorted
        self.w_src_sorted = supporting_safe_move_w_src_sorted
        self.w_gap = supporting_safe_move_w_gap
        self.w_fill = supporting_safe_move_w_fill
        self.w_src_ub = supporting_safe_move_w_src_ub
        self.w_src_bad = supporting_safe_move_w_src_bad
        self.w_dest_fill = supporting_safe_move_w_dest_fill
        self.max_bad_increase = supporting_safe_move_max_bad_increase
        self.prefer_safe_only = supporting_safe_move_prefer_safe_only

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
        src_ub = partial.ub(so)
        src_bad = partial.h(so) - partial.sorted_n[so]
        src_sorted = 1 if partial.is_sorted_stack(so) else 0
        dst_sorted_before = 1 if partial.is_sorted_stack(sd) else 0
        dst_sorted_after = 1 if trial.is_sorted_stack(sd) else 0
        moved = partial.g(so)
        dest_top_before = partial.g(sd) if partial.stacks[sd] else partial.G
        gap = max(0, dest_top_before - moved)
        fill_after = trial.h(sd)
        return (self.w_bad * bad_delta + self.w_ub * ub_delta, -self.w_src_ub * src_ub, -self.w_src_bad * src_bad, src_sorted, -self.w_dest_sorted * dst_sorted_after, -self.w_fill * fill_after, -self.w_dest_fill * partial.e(sd), self.w_gap * gap, self.w_src_sorted * (1 - dst_sorted_before), so, sd)

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
        if self.prefer_safe_only and safe_candidates:
            safe_candidates.sort(key=lambda x: x[0])
            return [Move(so=so, sd=sd) for _, so, sd in safe_candidates]
        if not candidates:
            return []
        candidates.sort(key=lambda x: x[0])
        return [Move(so=so, sd=sd) for _, so, sd in candidates]

class SafePlacementTransitions:

    def initial(self, partial):
        return ()

    def select(self, partial, memory, rules):
        if rules.applies(SupportingSafeMoveRule.name):
            return (SupportingSafeMoveRule.name, memory)
        return (FALLBACK, memory)

def build_component(problem, **params):
    rule = SupportingSafeMoveRule(problem, **params)
    transitions = SafePlacementTransitions()
    return RuleMachine(problem, [rule], transitions)
