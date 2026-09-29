COMPONENT = {
    "name": "unblock_bad_below_move",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {},
}

from core.rules import RuleMachine


class UnblockBadBelowMove:
    """Mueve un tope bien puesto desde una pila que aún tiene contenedores mal puestos debajo."""

    name = "unblock_bad_below_move"

    def _is_bad(self, stack, idx):
        if idx == 0:
            return False
        return stack[idx] > stack[idx - 1]

    def _has_bad_below_top(self, stack):
        if len(stack) < 2:
            return False
        return any(self._is_bad(stack, i) for i in range(1, len(stack)))

    def _well_placed_top(self, stack):
        if not stack:
            return False
        if len(stack) == 1:
            return True
        return stack[-1] <= stack[-2]

    def allowed(self, partial, memory, candidates):
        stacks = partial.stacks
        out = []
        for a in candidates:
            so, sd = a.so, a.sd
            if so == sd:
                continue
            src = stacks[so]
            dst = stacks[sd]
            if not src:
                continue
            if not self._has_bad_below_top(src):
                continue
            moved = src[-1]
            if len(dst) >= partial.H:
                continue
            if dst and moved > dst[-1]:
                continue
            if not self._well_placed_top(src):
                continue
            out.append(a)
        return out


def build_component(problem, **params):
    return RuleMachine(problem, [UnblockBadBelowMove()])
