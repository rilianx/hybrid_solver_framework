from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from core.machine import FALLBACK
from core.rules import RuleMachine

@dataclass(frozen=True)
class Move:
    so: int
    sd: int
COMPONENT = {'name': 'singleton_release_priority_v1', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'w_dest_gap': {'type': 'float', 'range': [0.0, 10.0], 'default': 1.5}, 'w_fill': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.5}, 'w_future': {'type': 'float', 'range': [0.0, 10.0], 'default': 1.0}}}

class SingletonReleaseRule:
    name = 'singleton_release'

    def __init__(self, problem, w_dest_gap: float=1.5, w_fill: float=0.5, w_future: float=1.0, max_source_height: int=2, singleton_bonus: float=2.0):
        self.problem = problem
        self.w_dest_gap = w_dest_gap
        self.w_fill = w_fill
        self.w_future = w_future
        self.max_source_height = max_source_height
        self.singleton_bonus = singleton_bonus

    def init(self, partial):
        return ()

    def start(self, partial, memory):
        return memory

    def update(self, partial, memory, action):
        return memory

    def done(self, partial, memory):
        return True

    def _future_support(self, partial) -> int:
        count = 0
        for so in range(partial.S):
            if not partial.stacks[so]:
                continue
            c = partial.g(so)
            for sd in range(partial.S):
                if so == sd or len(partial.stacks[sd]) >= partial.H:
                    continue
                if not partial.stacks[sd]:
                    continue
                if partial.is_sorted_stack(sd) and c <= partial.g(sd):
                    count += 1
        return count

    def _candidate_key(self, partial, so: int, sd: int):
        c = partial.g(so)
        dest_top = partial.g(sd)
        trial = partial.copy(track=False)
        trial.move(so, sd)
        fill_after = trial.h(sd)
        future = self._future_support(trial)
        gap = dest_top - c
        score = self.w_dest_gap * gap + self.w_fill * fill_after - self.w_future * future
        if partial.h(so) == 1:
            score -= self.singleton_bonus
        return (score, gap, -future, fill_after, so * partial.S + sd)

    def propose(self, partial, memory):
        candidates: List[Tuple[tuple, int, int]] = []
        for so in range(partial.S):
            if not partial.stacks[so]:
                continue
            if partial.h(so) > self.max_source_height:
                continue
            if not partial.is_sorted_stack(so):
                continue
            if partial.h(so) != 1:
                continue
            for sd in range(partial.S):
                if so == sd:
                    continue
                if not partial.stacks[sd]:
                    continue
                if not partial.valid(so, sd):
                    continue
                c = partial.g(so)
                if c > partial.g(sd):
                    continue
                candidates.append((self._candidate_key(partial, so, sd), so, sd))
        candidates.sort(key=lambda x: x[0])
        return [Move(so=so, sd=sd) for _, so, sd in candidates]

class SupportingSafeMoveRule:
    _auto_supporting_safe_move_candidate_key_k1 = 0.5
    _auto_supporting_safe_move_candidate_key_k2 = 0.25
    name = 'supporting_safe_move'

    def __init__(self, problem, w_bad: float=4.0, w_ub: float=2.0, w_sorted: float=1.0, w_fill: float=0.5, w_src_ub: float=1.5, w_dest_top: float=0.25, w_future: float=1.25, w_dest_sorted: float=2.0, w_source_sorted: float=0.75, safe_margin: int=0):
        self.problem = problem
        self.w_bad = w_bad
        self.w_ub = w_ub
        self.w_sorted = w_sorted
        self.w_fill = w_fill
        self.w_src_ub = w_src_ub
        self.w_dest_top = w_dest_top
        self.w_future = w_future
        self.w_dest_sorted = w_dest_sorted
        self.w_source_sorted = w_source_sorted
        self.safe_margin = safe_margin

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

    def _future_support(self, partial) -> int:
        count = 0
        for so in range(partial.S):
            if not partial.stacks[so]:
                continue
            c = partial.g(so)
            for sd in range(partial.S):
                if so == sd or len(partial.stacks[sd]) >= partial.H:
                    continue
                if not partial.stacks[sd]:
                    continue
                if partial.is_sorted_stack(sd) and c <= partial.g(sd):
                    count += 1
        return count

    def _candidate_key(self, partial, so: int, sd: int):
        trial = partial.copy(track=False)
        trial.move(so, sd)
        base_bad = partial.bad()
        base_ub = self._total_ub(partial)
        new_bad = trial.bad()
        new_ub = self._total_ub(trial)
        new_sorted = sum(trial.sorted_n)
        future = self._future_support(trial)
        src_ub = partial.ub(so)
        dest_top = partial.g(sd)
        fill_after = trial.h(sd)
        dest_sorted_before = 1 if partial.is_sorted_stack(sd) else 0
        source_sorted_before = 1 if partial.is_sorted_stack(so) else 0
        delta_bad = new_bad - base_bad
        delta_ub = new_ub - base_ub
        score = self.w_bad * delta_bad + self.w_ub * delta_ub - self.w_sorted * new_sorted - self.w_future * future + self.w_fill * fill_after - self.w_src_ub * src_ub - self.w_dest_top * dest_top - self.w_dest_sorted * dest_sorted_before - self.w_source_sorted * source_sorted_before
        if source_sorted_before and (not dest_sorted_before) and (new_bad >= base_bad):
            score += float(self.safe_margin) + self._auto_supporting_safe_move_candidate_key_k1
        if partial.h(so) <= 2:
            score -= self._auto_supporting_safe_move_candidate_key_k2
        return (score, new_bad, new_ub, -new_sorted, -future, -dest_sorted_before, -source_sorted_before, fill_after, src_ub, dest_top, so * partial.S + sd)

    def propose(self, partial, memory):
        candidates: List[Tuple[tuple, int, int]] = []
        for so in range(partial.S):
            if not partial.stacks[so]:
                continue
            for sd in range(partial.S):
                if so == sd:
                    continue
                if not partial.stacks[sd]:
                    continue
                if not partial.valid(so, sd):
                    continue
                candidates.append((self._candidate_key(partial, so, sd), so, sd))
        candidates.sort(key=lambda x: x[0])
        return [Move(so=so, sd=sd) for _, so, sd in candidates]

class PriorityTransitions:

    def __init__(self, primary_rule: str, fallback_rule: str):
        self.primary_rule = primary_rule
        self.fallback_rule = fallback_rule

    def initial(self, partial):
        return ()

    def select(self, partial, memory, rules):
        if rules.applies(self.primary_rule):
            return (self.primary_rule, memory)
        if rules.applies(self.fallback_rule):
            return (self.fallback_rule, memory)
        return (FALLBACK, memory)

def _build_component_llm(problem, **params):
    primary = SingletonReleaseRule(problem, **params)
    fallback = SupportingSafeMoveRule(problem)
    transitions = PriorityTransitions(SingletonReleaseRule.name, SupportingSafeMoveRule.name)
    return RuleMachine(problem, [primary, fallback], transitions)

def build_component(problem, **params):
    return _build_component_llm(problem, **params)
