from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from core.machine import FALLBACK
from core.rules import RuleMachine

@dataclass(frozen=True)
class Move:
    so: int
    sd: int
COMPONENT = {'name': 'supporting_safe_move_refined', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'w_ub': {'type': 'float', 'range': [0.0, 10.0], 'default': 2.0}, 'w_fill': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.5}, 'w_src_ub': {'type': 'float', 'range': [0.0, 10.0], 'default': 1.5}, 'w_dest_top': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.25}}}

class SupportingSafeMoveRule:
    name = 'supporting_safe_move'

    def __init__(self, problem, w_bad: float=4.0, w_ub: float=2.0, w_sorted: float=1.0, w_fill: float=0.5, w_src_ub: float=1.5, w_dest_top: float=0.25, safe_margin: int=0):
        self.problem = problem
        self.w_bad = w_bad
        self.w_ub = w_ub
        self.w_sorted = w_sorted
        self.w_fill = w_fill
        self.w_src_ub = w_src_ub
        self.w_dest_top = w_dest_top
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

    def propose(self, partial, memory):
        """
        Ordena por simulación directa del efecto del movimiento:
        - prioriza reducir la cota inferior bad()
        - luego reduce contenedores mal puestos desbloqueados
        - luego aumenta/ preserva tramos ordenados
        - en empate, prefiere movimientos que vacían o aligeran pilas conflictivas
        """
        candidates: List[Tuple[float, int, int, int, int, int, int]] = []
        base_bad = partial.bad()
        base_ub = self._total_ub(partial)
        for so in range(partial.S):
            if not partial.stacks[so]:
                continue
            c = partial.g(so)
            src_ub = partial.ub(so)
            for sd in range(partial.S):
                if not partial.valid(so, sd):
                    continue
                trial = partial.copy(track=False)
                trial.move(so, sd)
                new_bad = trial.bad()
                new_ub = self._total_ub(trial)
                new_sorted = sum(trial.sorted_n)
                fill_after = trial.h(sd)
                dest_top = trial.g(sd) if trial.stacks[sd] else trial.G
                delta_bad = new_bad - base_bad
                delta_ub = new_ub - base_ub
                score = self.w_bad * delta_bad + self.w_ub * delta_ub - self.w_sorted * new_sorted + self.w_fill * fill_after - self.w_src_ub * src_ub - self.w_dest_top * dest_top
                if partial.is_sorted_stack(so) and (not partial.is_sorted_stack(sd)):
                    score += float(self.safe_margin)
                candidates.append((score, new_bad, new_ub, -new_sorted, -src_ub, dest_top, so * partial.S + sd))
        candidates.sort()
        return [Move(so=item[-1] // partial.S, sd=item[-1] % partial.S) for item in candidates]

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
