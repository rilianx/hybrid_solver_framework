from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from core.machine import FALLBACK
from core.rules import RuleMachine

@dataclass(frozen=True)
class Move:
    so: int
    sd: int
COMPONENT = {'name': 'supporting_safe_move_refined_v7', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {}}

class SupportingSafeMoveRule:
    name = 'supporting_safe_move'

    def __init__(self, problem, supporting_safe_move_w_bad: float=8.0, supporting_safe_move_w_ub: float=6.0, supporting_safe_move_w_dest_sorted: float=1.5, supporting_safe_move_w_src_sorted: float=2.5, supporting_safe_move_w_gap: float=1.0, supporting_safe_move_w_fill: float=0.75, supporting_safe_move_max_bad_increase: int=1, supporting_safe_move_prefer_safe_only: bool=True):
        self.problem = problem
        self.w_bad = supporting_safe_move_w_bad
        self.w_ub = supporting_safe_move_w_ub
        self.w_dest_sorted = supporting_safe_move_w_dest_sorted
        self.w_src_sorted = supporting_safe_move_w_src_sorted
        self.w_gap = supporting_safe_move_w_gap
        self.w_fill = supporting_safe_move_w_fill
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
        src_sorted = partial.is_sorted_stack(so)
        dst_sorted_before = partial.is_sorted_stack(sd)
        dst_sorted_after = trial.is_sorted_stack(sd)
        moved = partial.g(so)
        dest_top_before = partial.g(sd) if partial.stacks[sd] else partial.G
        gap = max(0, dest_top_before - moved)
        dst_fill_before = partial.h(sd)
        dst_fill_after = trial.h(sd)
        dst_sorted_gain = trial.sorted_n[sd] - partial.sorted_n[sd]
        return (bad_delta, ub_delta, 0 if dst_sorted_after else 1, -dst_sorted_gain, 0 if dst_sorted_before else 1, 1 if src_sorted else 0, gap, -dst_fill_after, -dst_fill_before, so, sd)

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

def build_component(problem, **params):
    rule = SupportingSafeMoveRule(problem, **params)
    transitions = SafePlacementTransitions()
    return RuleMachine(problem, [rule], transitions)
