from __future__ import annotations

from dataclasses import dataclass
from math import inf
from typing import Any


COMPONENT = {
    "name": "target_stack_clearance_policy",
    "slot": "construction_policy",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "target_bias": {"type": "float", "range": [0.5, 5.0]},
        "block_penalty": {"type": "float", "range": [0.5, 10.0]},
    },
}


@dataclass(frozen=True)
class _Memory:
    mode: str
    target: int
    target_group: int
    patience: int


class TargetStackClearancePolicy:
    """Política constructiva con memoria que fija una pila objetivo y la despeja de forma persistente.

    Idea:
    - elige una pila no ordenada como objetivo;
    - mientras siga teniendo contenedores mal apilados, prioriza mover su tope si está bloqueando
      o, si no lo está, recolocar el tope de otras pilas hacia destinos que no creen nuevas violaciones;
    - cuando la pila objetivo queda ordenada, cambia a la siguiente pila desordenada.

    La memoria guarda el objetivo actual y una pequeña paciencia para evitar aferrarse a un plan
    cuando ya no aporta mejora.
    """

    def __init__(self, problem, target_bias: float = 1.5, block_penalty: float = 2.5):
        self.problem = problem
        self.inst = problem.inst
        self.target_bias = float(target_bias)
        self.block_penalty = float(block_penalty)

    def _ordered(self, stack: tuple[int, ...]) -> bool:
        return all(stack[i] >= stack[i + 1] for i in range(len(stack) - 1))

    def _disorder(self, stacks: tuple[tuple[int, ...], ...]) -> int:
        return sum(1 for s in stacks for i in range(len(s) - 1) if s[i] < s[i + 1])

    def _top(self, partial, idx: int) -> int | None:
        s = partial.stacks[idx]
        return s[-1] if s else None

    def _pick_target(self, partial) -> tuple[int, int]:
        best = None
        best_key = None
        for i, s in enumerate(partial.stacks):
            if self._ordered(s):
                continue
            # target = pila con más desorden local y tope relativamente pequeño
            local_bad = sum(1 for j in range(len(s) - 1) if s[j] < s[j + 1])
            top = s[-1] if s else -1
            key = (-local_bad, top, len(s), i)
            if best is None or key < best_key:
                best = (i, top)
                best_key = key
        if best is None:
            # if all ordered, default harmless
            return (0, 0)
        return best

    def init(self, partial: Any) -> _Memory:
        target, tg = self._pick_target(partial)
        return _Memory(mode="clear_target", target=int(target), target_group=int(tg), patience=0)

    def score(self, partial: Any, memory: _Memory, action: Any) -> float:
        so, sd = int(action[0]), int(action[1])
        inst = self.inst
        x = partial.stacks[so][-1]
        dst_top = partial.stacks[sd][-1] if partial.stacks[sd] else None

        score = 0.0

        # Prefer to work on the current target stack.
        if so == memory.target:
            score -= self.target_bias
            # If moving the blocking top from the target, strongly prefer it.
            score -= self.block_penalty
        elif sd == memory.target:
            # moving something onto the target usually hurts the plan
            score += self.block_penalty

        # Moves that keep the destination orderly are preferred.
        if dst_top is None or dst_top >= x:
            score -= 0.25
        else:
            score += 1.25

        # Prefer destinations that are not the current target unless that is the only good outlet.
        if sd != memory.target and len(partial.stacks[sd]) < inst.H:
            score -= 0.05

        # If the source is already ordered, discourage touching it.
        if self._ordered(partial.stacks[so]):
            score += 0.5

        # Mild preference for increasing overall order.
        nxt_dis = 0
        for i, s in enumerate(partial.stacks):
            if i == so:
                tmp = list(s)
                tmp.pop()
                if sd == i:
                    tmp.append(x)
                s_eval = tuple(tmp)
            elif i == sd:
                tmp = list(s)
                tmp.append(x)
                s_eval = tuple(tmp)
            else:
                s_eval = s
            nxt_dis += sum(1 for j in range(len(s_eval) - 1) if s_eval[j] < s_eval[j + 1])

        score += 0.1 * nxt_dis
        return float(score)

    def update(self, partial: Any, memory: _Memory, action: Any) -> _Memory:
        so, sd = int(action[0]), int(action[1])

        # Re-anchor the target if it is already ordered or was just fully cleared.
        if so == memory.target:
            nxt_stack = list(partial.stacks[so])
            nxt_stack.pop()
            nxt_disordered = any(nxt_stack[i] < nxt_stack[i + 1] for i in range(len(nxt_stack) - 1))
            if not nxt_disordered:
                target, tg = self._pick_target(_PartialLike(partial.stacks, so))
                return _Memory(mode="clear_target", target=int(target), target_group=int(tg), patience=0)
            return _Memory(mode=memory.mode, target=memory.target, target_group=memory.target_group, patience=0)

        # If another action touched the target, keep the plan but raise patience.
        if sd == memory.target:
            patience = min(memory.patience + 1, 3)
            if patience >= 2:
                target, tg = self._pick_target(partial)
                return _Memory(mode="clear_target", target=int(target), target_group=int(tg), patience=0)
            return _Memory(mode=memory.mode, target=memory.target, target_group=memory.target_group, patience=patience)

        return _Memory(mode=memory.mode, target=memory.target, target_group=memory.target_group, patience=memory.patience)


@dataclass(frozen=True)
class _PartialLike:
    stacks: tuple[tuple[int, ...], ...]
    depth: int = 0


def build_component(problem, target_bias: float = 1.5, block_penalty: float = 2.5):
    return TargetStackClearancePolicy(problem, target_bias=target_bias, block_penalty=block_penalty)
