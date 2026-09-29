from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from core.machine import FALLBACK
from core.rules import RuleMachine

@dataclass(frozen=True)
class Move:
    so: int
    sd: int
COMPONENT = {'name': 'supporting_safe_move_refined_v2', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'w_fill': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.5}, 'w_dest_top': {'type': 'float', 'range': [0.0, 10.0], 'default': 0.25}, 'supporting_safe_move_propose_k1': {'type': 'float', 'range': [0.0, 120.0], 'default': 60.0}, 'supporting_safe_move_propose_k4': {'type': 'float', 'range': [0.0, 12.0], 'default': 6.0}}}

class SupportingSafeMoveRule:
    _auto_supporting_safe_move_propose_k1 = 60.0
    _auto_supporting_safe_move_propose_k2 = 25.0
    _auto_supporting_safe_move_propose_k3 = 8.0
    _auto_supporting_safe_move_propose_k4 = 6.0
    _auto_supporting_safe_move_propose_k5 = 5.0
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
        Orden de preferencia refinado:

        1) Primero, movimientos que no empeoran la cota inferior de contenedores mal puestos
           (bad) y, si hay empate, los que reducen más la suma de ub.
        2) Entre esos, favorece colocar sobre pilas ya ordenadas con la menor holgura posible
           (top más cercano al contenedor movido), porque suele preservar futuras extensiones
           seguras.
        3) Evita mover desde una pila ya ordenada salvo que sea claramente mejor.
        4) Como desempate, prioriza vaciar/ aligerar pilas con mayor ub.
        """
        candidates: List[Tuple[Tuple[float, ...], int, int]] = []
        base_bad = partial.bad()
        base_ub = self._total_ub(partial)
        base_sorted = sum(partial.sorted_n)
        for so in range(partial.S):
            if not partial.stacks[so]:
                continue
            src_sorted = partial.is_sorted_stack(so)
            src_ub = partial.ub(so)
            top = partial.g(so)
            for sd in range(partial.S):
                if not partial.valid(so, sd):
                    continue
                trial = partial.copy(track=False)
                trial.move(so, sd)
                new_bad = trial.bad()
                new_ub = self._total_ub(trial)
                new_sorted = sum(trial.sorted_n)
                dest_before_sorted = partial.is_sorted_stack(sd)
                dest_after_sorted = trial.is_sorted_stack(sd)
                dest_top_before = partial.g(sd) if partial.stacks[sd] else partial.G
                bad_inc = max(0, new_bad - base_bad)
                ub_inc = max(0, new_ub - base_ub)
                bad_dec = max(0, base_bad - new_bad)
                ub_dec = max(0, base_ub - new_ub)
                dest_bonus = 0
                if dest_after_sorted:
                    dest_bonus -= 2
                elif dest_before_sorted:
                    dest_bonus -= 1
                if partial.stacks[sd]:
                    gap = max(0, partial.g(sd) - top)
                else:
                    gap = max(0, partial.G - top)
                score = 1000.0 * bad_inc + 100.0 * ub_inc - self._auto_supporting_safe_move_propose_k1 * bad_dec - self._auto_supporting_safe_move_propose_k2 * ub_dec - self._auto_supporting_safe_move_propose_k3 * new_sorted + self._auto_supporting_safe_move_propose_k4 * gap + self._auto_supporting_safe_move_propose_k5 * (1 if src_sorted else 0) + 2.0 * (1 if not dest_after_sorted else 0) - self.w_src_ub * src_ub - self.w_dest_top * dest_top_before + self.w_fill * partial.h(sd) - self.w_sorted * base_sorted + self.safe_margin * (1 if src_sorted and (not dest_after_sorted) else 0)
                candidates.append(((score, new_bad, new_ub, -new_sorted, 1 if src_sorted else 0, 0 if dest_after_sorted else 1, gap, so, sd), so, sd))
        candidates.sort(key=lambda x: x[0])
        return [Move(so=item[1], sd=item[2]) for item in candidates]

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
_AUTO = {'supporting_safe_move_propose_k1': 60.0, 'supporting_safe_move_propose_k2': 25.0, 'supporting_safe_move_propose_k3': 8.0, 'supporting_safe_move_propose_k4': 6.0, 'supporting_safe_move_propose_k5': 5.0}
_AUTO_OWNER = {'supporting_safe_move_propose_k1': 'SupportingSafeMoveRule', 'supporting_safe_move_propose_k2': 'SupportingSafeMoveRule', 'supporting_safe_move_propose_k3': 'SupportingSafeMoveRule', 'supporting_safe_move_propose_k4': 'SupportingSafeMoveRule', 'supporting_safe_move_propose_k5': 'SupportingSafeMoveRule'}
_AUTO_CLASSES = {'SupportingSafeMoveRule': SupportingSafeMoveRule}

def build_component(problem, **params):
    """Envoltura del framework: los números que el LLM dejó sueltos en los métodos son parámetros
    (`_AUTO`, declarados en COMPONENT; `_AUTO_OWNER`: la clase de cada uno). Se fijan en las clases
    mientras se construye (por si un `__init__` los usa) y en cada instancia: la máquina, sus
    reglas y sus transiciones."""
    auto = {k: params.pop(k, v) for k, v in _AUTO.items()}
    saved = {k: getattr(_AUTO_CLASSES[_AUTO_OWNER[k]], '_auto_' + k) for k in auto}
    for k, v in auto.items():
        setattr(_AUTO_CLASSES[_AUTO_OWNER[k]], '_auto_' + k, v)
    try:
        obj = _build_component_llm(problem, **params)
    finally:
        for k, v in saved.items():
            setattr(_AUTO_CLASSES[_AUTO_OWNER[k]], '_auto_' + k, v)
    parts = [obj, getattr(obj, 'transitions', None), *list(getattr(obj, 'rules', None) or [])]
    for part in parts:
        for k, v in auto.items():
            if part is not None and isinstance(part, _AUTO_CLASSES[_AUTO_OWNER[k]]):
                setattr(part, '_auto_' + k, v)
    return obj
