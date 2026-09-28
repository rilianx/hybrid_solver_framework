from core.machine import FALLBACK

COMPONENT = {
    "name": "good_placement_state",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {},
}


class GoodPlacementState:
    """Un único estado: intenta colocar contenedores en pilas donde queden bien puestos.
    Si ya no hay una acción de este tipo, delega al comodín del framework."""

    states = ("place_well",)

    def __init__(self, problem):
        self.problem = problem

    def initial(self, partial):
        return "place_well", ()

    def transition(self, partial, state, memory):
        if state != "place_well":
            return FALLBACK, ()
        if partial.is_sorted():
            return FALLBACK, ()

        for so in range(partial.S):
            if not partial.stacks[so]:
                continue
            c = partial.stacks[so][-1]
            for sd in range(partial.S):
                if not partial.valid(so, sd):
                    continue
                if partial.h(sd) == 0 or c <= partial.g(sd):
                    return "place_well", ()
        return FALLBACK, ()

    def score(self, partial, state, memory, action):
        if state != "place_well":
            return 0.0

        so, sd = action.so, action.sd
        c = partial.stacks[so][-1]

        make_sorted = 1 if partial.h(sd) == 0 or c <= partial.g(sd) else 0
        src_bad = partial.ub(so)
        dst_space = partial.e(sd)

        sim = partial.copy(track=False)
        sim.move(so, sd)
        after_bad = sim.bad()

        return (
            1000.0 * (1 - make_sorted)
            + 100.0 * after_bad
            + 10.0 * src_bad
            - 1.0 * dst_space
            + 0.01 * sd
        )

    def update(self, partial, state, memory, action):
        return memory


def build_component(problem, **params):
    return GoodPlacementState(problem)

