COMPONENT = {
    "name": "repair_bad_top_move",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {},
}

from core.rules import RuleMachine


class RepairBadTopMove:
    """Mueve un tope mal puesto a una pila donde quede bien puesto."""

    name = "repair_bad_top_move"

    def allowed(self, partial, memory, candidates):
        if not candidates:
            return []

        stacks = partial.stacks
        h = partial.h
        G = partial.G

        def top_group(i):
            return G if h(i) == 0 else stacks[i][-1]

        def is_well_placed_at(i, grp):
            if h(i) == 0:
                return True
            return top_group(i) >= grp

        def is_bad_top_source(so):
            if h(so) == 0:
                return False
            grp = stacks[so][-1]
            if h(so) == 1:
                return False
            return stacks[so][-2] < grp

        filtered = []
        for a in candidates:
            so = a.so
            sd = a.sd
            if so == sd:
                continue
            if h(so) == 0 or h(sd) >= partial.H:
                continue
            if not is_bad_top_source(so):
                continue

            moved = stacks[so][-1]
            if not is_well_placed_at(sd, moved):
                continue

            # Evita empeorar pilas ya ordenadas si hay alternativa
            if partial.is_sorted_stack(so) and not partial.is_sorted_stack(sd):
                continue

            filtered.append(a)

        if not filtered:
            return []

        def key(a):
            so = a.so
            sd = a.sd
            moved = stacks[so][-1]
            dest_top = top_group(sd)
            # preferir vacías, luego destinos más "altos", luego reducir huecos
            empty_bonus = 0 if h(sd) == 0 else 1
            tighten = abs(dest_top - moved)
            return (empty_bonus, tighten, h(sd), sd)

        filtered.sort(key=key)
        return filtered


def build_component(problem, **params):
    return RuleMachine(problem, [RepairBadTopMove()])
