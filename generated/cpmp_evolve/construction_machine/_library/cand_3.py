COMPONENT = {
    "name": "move_bad_top_to_bad_stack",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {},
}

from core.rules import RuleMachine


class MoveBadTopToBadStack:
    """Mueve un tope mal puesto a una pila donde seguirá mal puesto."""

    name = "move_bad_top_to_bad_stack"

    def allowed(self, partial, memory, candidates):
        stacks = partial.stacks
        h = partial.h
        sorted_n = partial.sorted_n

        def is_bad_top(i):
            return h(i) > 0 and sorted_n[i] < h(i)

        def dest_is_bad_for(group, j):
            if h(j) >= partial.H:
                return False
            if h(j) == 0:
                return False
            return stacks[j][-1] < group

        allowed = []
        for a in candidates:
            so = a.so
            sd = a.sd
            if so == sd:
                continue
            if not is_bad_top(so):
                continue
            if not dest_is_bad_for(stacks[so][-1], sd):
                continue
            allowed.append(a)

        allowed.sort(key=lambda a: (
            -stacks[a.sd][-1],          # destino más "alto" posible, pero aún malo
            -sorted_n[a.so],            # tope más claramente mal situado
            a.so,
            a.sd,
        ))
        return allowed


def build_component(problem, **params):
    return RuleMachine(problem, [MoveBadTopToBadStack()])
