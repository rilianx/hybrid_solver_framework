from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from core.machine import FALLBACK
from core.rules import RuleMachine

@dataclass(frozen=True)
class Move:
    so: int
    sd: int
COMPONENT = {'name': 'supporting_safe_move_refined_v8_short_source_unlock', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'short_source_unlock_short_source_min_height': {'type': 'int', 'range': [0, 4], 'default': 2}}}

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

class ShortSourceUnlockRule:
    name = 'short_source_unlock'

    def __init__(self, problem, short_source_min_height: int=2):
        self.problem = problem
        self.short_source_min_height = short_source_min_height

    def init(self, partial):
        return ()

    def start(self, partial, memory):
        best = None
        best_key = None
        for so in range(partial.S):
            if not partial.stacks[so]:
                continue
            if not partial.is_sorted_stack(so):
                continue
            h = partial.h(so)
            if h < self.short_source_min_height:
                continue
            top = partial.g(so)
            key = (h, top, so)
            if best_key is None or key < best_key:
                best_key = key
                best = so
        return () if best is None else (best,)

    def update(self, partial, memory, action):
        return ()

    def done(self, partial, memory):
        return True

    def propose(self, partial, memory):
        if not memory:
            return []
        so = memory[0]
        if so < 0 or so >= partial.S or (not partial.stacks[so]):
            return []
        candidates: List[Tuple[Tuple, int, int]] = []
        base_bad = partial.bad()
        for sd in range(partial.S):
            if not partial.valid(so, sd):
                continue
            trial = partial.copy(track=False)
            trial.move(so, sd)
            bad_delta = trial.bad() - base_bad
            dst_sorted_after = trial.is_sorted_stack(sd)
            dst_sorted_gain = trial.sorted_n[sd] - partial.sorted_n[sd]
            moved = partial.g(so)
            dest_top = partial.g(sd) if partial.stacks[sd] else partial.G
            gap = max(0, dest_top - moved)
            score = (bad_delta, 0 if dst_sorted_after else 1, -dst_sorted_gain, gap, -trial.h(sd), sd)
            candidates.append((score, so, sd))
        candidates.sort(key=lambda x: x[0])
        return [Move(so=so, sd=sd) for _, so, sd in candidates]

class SafePlacementTransitions:

    def __init__(self):
        self.order = (ShortSourceUnlockRule.name, SupportingSafeMoveRule.name)

    def initial(self, partial):
        return ()

    def select(self, partial, memory, rules):
        if rules.active == ShortSourceUnlockRule.name and (not rules.done(ShortSourceUnlockRule.name)):
            return (ShortSourceUnlockRule.name, memory)
        if rules.applies(ShortSourceUnlockRule.name):
            return (ShortSourceUnlockRule.name, memory)
        if rules.applies(SupportingSafeMoveRule.name):
            return (SupportingSafeMoveRule.name, memory)
        return (FALLBACK, memory)

def _build_component_llm(problem, **params):
    unlock_rule = ShortSourceUnlockRule(problem, **{k: v for k, v in params.items() if k.startswith('short_source_')})
    safe_rule = SupportingSafeMoveRule(problem, **{k: v for k, v in params.items() if k.startswith('supporting_safe_move_')})
    transitions = SafePlacementTransitions()
    return RuleMachine(problem, [unlock_rule, safe_rule], transitions)

_AUTO = {'short_source_unlock_short_source_min_height': 2}
_AUTO_OWNER = {'short_source_unlock_short_source_min_height': 'ShortSourceUnlockRule'}
_AUTO_ATTR = {'short_source_unlock_short_source_min_height': 'short_source_min_height'}
_AUTO_CLASSES = {'ShortSourceUnlockRule': ShortSourceUnlockRule}
_AUTO_FACTORY = '_build_component_llm'

def build_component(problem, **params):
    """Envoltura del framework: los números que el LLM dejó sueltos en los métodos son parámetros
    (`_AUTO`, declarados en COMPONENT; `_AUTO_OWNER`: la clase de cada uno). Se fijan en las clases
    mientras se construye (por si un `__init__` los usa) y en cada instancia: la máquina, sus
    reglas y sus transiciones."""
    attrs = globals().get("_AUTO_ATTR", {})  # parámetro -> atributo de la instancia (los defaults de un __init__)
    auto = {k: params.pop(k, v) for k, v in _AUTO.items()}
    lifted = [k for k in auto if k not in attrs]
    saved = {k: getattr(_AUTO_CLASSES[_AUTO_OWNER[k]], "_auto_" + k) for k in lifted}
    for k in lifted:
        setattr(_AUTO_CLASSES[_AUTO_OWNER[k]], "_auto_" + k, auto[k])
    try:
        obj = _build_component_llm(problem, **params)
    finally:
        for k, v in saved.items():
            setattr(_AUTO_CLASSES[_AUTO_OWNER[k]], "_auto_" + k, v)
    parts = [obj, getattr(obj, "transitions", None), *list(getattr(obj, "rules", None) or [])]
    for part in parts:
        for k, v in auto.items():
            if part is not None and isinstance(part, _AUTO_CLASSES[_AUTO_OWNER[k]]):
                setattr(part, attrs.get(k, "_auto_" + k), v)
    return obj
