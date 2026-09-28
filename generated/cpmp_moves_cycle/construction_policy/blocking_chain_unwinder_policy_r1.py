from __future__ import annotations

from dataclasses import dataclass
from typing import Any


COMPONENT = {
    "name": "blocking_chain_unwinder_policy",
    "slot": "construction_policy",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "chain_priority": {"type": "float", "range": [0.5, 8.0]},
        "destination_slack": {"type": "float", "range": [0.0, 2.0]},
    },
}


@dataclass(frozen=True)
class _Memory:
    source: int
    anchor: int
    stage: int  # 0 = remove blockers, 1 = finish the source
    lock: int


class BlockingChainUnwinderPolicy:
    """Política que persigue una cadena de bloqueos: elige una pila fuente y vacía su parte mala.

    Idea:
    - selecciona una pila con una 'ruptura' alta entre dos contenedores adyacentes;
    - mientras esté en stage 0, prioriza mover desde esa pila a un destino que no empeore el orden;
    - cuando el tope de la fuente ya no bloquea, pasa a stage 1 y termina de estabilizar esa pila.

    Esto es estructuralmente distinto a una política de 'pila objetivo': aquí la memoria guarda una
    fuente concreta y un ancla de orden.
    """

    def __init__(self, problem, chain_priority: float = 2.0, destination_slack: float = 0.5):
        self.problem = problem
        self.inst = problem.inst
        self.chain_priority = float(chain_priority)
        self.destination_slack = float(destination_slack)

    def _ordered(self, stack: tuple[int, ...]) -> bool:
        return all(stack[i] >= stack[i + 1] for i in range(len(stack) - 1))

    def _breaks(self, stack: tuple[int, ...]) -> int:
        return sum(1 for i in range(len(stack) - 1) if stack[i] < stack[i + 1])

    def _source_candidates(self, partial) -> list[tuple[int, int]]:
        out = []
        for i, s in enumerate(partial.stacks):
            if len(s) < 2:
                continue
            br = self._breaks(s)
            if br > 0:
                out.append((i, br))
        out.sort(key=lambda t: (-t[1], len(partial.stacks[t[0]]), t[0]))
        return out

    def init(self, partial: Any) -> _Memory:
        cand = self._source_candidates(partial)
        if cand:
            source = cand[0][0]
        else:
            source = 0
        stack = partial.stacks[source]
        anchor = stack[-2] if len(stack) >= 2 else (stack[-1] if stack else 0)
        return _Memory(source=int(source), anchor=int(anchor), stage=0, lock=0)

    def score(self, partial: Any, memory: _Memory, action: Any) -> float:
        so, sd = int(action[0]), int(action[1])
        x = partial.stacks[so][-1]
        dst_top = partial.stacks[sd][-1] if partial.stacks[sd] else None

        score = 0.0

        # Strongly focus on the selected source.
        if so == memory.source:
            score -= self.chain_priority
        else:
            score += 0.3

        # In stage 0, prefer moves that unblock the source top.
        if memory.stage == 0:
            if so == memory.source:
                score -= 1.0
            if sd == memory.source:
                score += 2.0

        # Prefer destinations that are safe or nearly safe.
        if dst_top is None or dst_top >= x:
            score -= 0.4
        else:
            score += 1.4

        # Avoid wasting capacity on already ordered piles if other options exist.
        if self._ordered(partial.stacks[sd]):
            score += 0.15

        # Tiny tie-breaker: prefer filling less loaded stacks.
        score += 0.01 * len(partial.stacks[sd])

        return float(score)

    def update(self, partial: Any, memory: _Memory, action: Any) -> _Memory:
        so, sd = int(action[0]), int(action[1])

        # If we moved from the current source, decide whether to keep unwinding it.
        if so == memory.source:
            src = partial.stacks[so]
            # If the current source is now ordered, switch to another blocking stack.
            if self._ordered(src[:-1]) if len(src) > 1 else True:
                candidates = self._source_candidates(partial)
                if candidates:
                    new_source = candidates[0][0]
                    new_stack = partial.stacks[new_source]
                    anchor = new_stack[-2] if len(new_stack) >= 2 else (new_stack[-1] if new_stack else 0)
                    return _Memory(source=int(new_source), anchor=int(anchor), stage=0, lock=0)
                return _Memory(source=memory.source, anchor=memory.anchor, stage=1, lock=0)
            return _Memory(source=memory.source, anchor=memory.anchor, stage=0, lock=0)

        # If another move changed the neighborhood of the source, increase lock and maybe retarget.
        lock = min(memory.lock + 1, 3)
        if lock >= 2:
            candidates = self._source_candidates(partial)
            if candidates:
                new_source = candidates[0][0]
                new_stack = partial.stacks[new_source]
                anchor = new_stack[-2] if len(new_stack) >= 2 else (new_stack[-1] if new_stack else 0)
                return _Memory(source=int(new_source), anchor=int(anchor), stage=0, lock=0)
        return _Memory(source=memory.source, anchor=memory.anchor, stage=memory.stage, lock=lock)


def build_component(problem, chain_priority: float = 2.0, destination_slack: float = 0.5):
    return BlockingChainUnwinderPolicy(problem, chain_priority=chain_priority, destination_slack=destination_slack)
