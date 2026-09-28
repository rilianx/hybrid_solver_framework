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
        best_i = None
        best_key = None
        for i, s in enumerate(partial.stacks):
            if not s:
                continue
            # Prioriza pilas que ya tengan una violación justo en el tope:
            # son objetivos más baratos de despejar que una pila "profundamente" desordenada.
            top = s[-1]
            below = s[-2] if len(s) >= 2 else inf
            local_bad = sum(1 for j in range(len(s) - 1) if s[j] < s[j + 1])
            top_blocking = 1 if len(s) >= 2 and s[-2] < s[-1] else 0
            # Menor key = mejor
            key = (
                0 if top_blocking else 1,   # primero, pilas donde el tope ya bloquea
                local_bad,                  # luego, menor desorden interno
                len(s),                     # luego, más cortas
                top,                       # y con tope pequeño
                i,
            )
            if best_key is None or key < best_key:
                best_key = key
                best_i = i

        if best_i is None:
            return (0, 0)

        return (int(best_i), int(partial.stacks[best_i][-1]))

    def init(self, partial: Any) -> _Memory:
        # Start from the most promising stack to clear: the one whose top is the
        # smallest among non-empty stacks, breaking ties by larger immediate disorder.
        # This keeps the policy conservative and close to a trivial constructive start.
        best_i = None
        best_key = None
        for i, s in enumerate(partial.stacks):
            if not s:
                continue
            local_bad = sum(1 for j in range(len(s) - 1) if s[j] < s[j + 1])
            key = (
                s[-1],                # prefer smaller tops
                -local_bad,           # but if tied, more locally disordered stacks first
                -len(s),              # then taller stacks
                i,
            )
            if best_key is None or key < best_key:
                best_key = key
                best_i = i

        if best_i is None:
            return _Memory(mode="clear_target", target=0, target_group=0, patience=0)

        return _Memory(
            mode="clear_target",
            target=int(best_i),
            target_group=int(partial.stacks[best_i][-1]),
            patience=0,
        )

    def score(self, partial: Any, memory: _Memory, action: Any) -> float:
        so, sd = int(action[0]), int(action[1])
        x = partial.stacks[so][-1]
        dst_top = partial.stacks[sd][-1] if partial.stacks[sd] else None

        score = 0.0

        # Mild memory: work on the target stack, but without making the policy overly rigid.
        if so == memory.target:
            score -= self.target_bias * 0.25
        if sd == memory.target:
            score += self.block_penalty * 0.15

        # Prefer destinations that preserve local order.
        if dst_top is None or dst_top >= x:
            score -= 0.2
        else:
            score += 0.8

        # Avoid touching already ordered source stacks too much.
        if self._ordered(partial.stacks[so]):
            score += 0.25

        # Prefer not to overfill the destination.
        if len(partial.stacks[sd]) >= self.inst.H:
            score += 10.0

        # Lightweight look-ahead: count resulting local violations.
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

        score += 0.05 * nxt_dis
        return float(score)

    def update(self, partial: Any, memory: _Memory, action: Any) -> _Memory:
        so, sd = int(action[0]), int(action[1])

        # If the target stack was touched, refresh the target only when that stack becomes ordered.
        if so == memory.target:
            nxt_stack = list(partial.stacks[so])
            if nxt_stack:
                nxt_stack.pop()
            nxt_disordered = any(nxt_stack[i] < nxt_stack[i + 1] for i in range(len(nxt_stack) - 1))
            if not nxt_disordered:
                target, tg = self._pick_target(_PartialLike(partial.stacks, so))
                return _Memory(mode="clear_target", target=int(target), target_group=int(tg), patience=0)
            return _Memory(mode=memory.mode, target=memory.target, target_group=memory.target_group, patience=0)

        # If the target receives a container, keep the same target but increase patience slightly.
        if sd == memory.target:
            patience = min(memory.patience + 1, 2)
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
