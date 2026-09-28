python
from core.machine import FALLBACK

COMPONENT = {
    "name": "one_step_stabilizer",
    "slot": "construction_machine",
    "compatible_skeletons": ["CONSTRUCT"],
    "requires": [],
    "params": {
        "good_move_bias": {"type": "float", "range": [0.0, 100.0], "default": 25.0},
        "sorted_destination_bias": {"type": "float", "range": [0.0, 100.0], "default": 10.0},
        "height_bias": {"type": "float", "range": [0.0, 100.0], "default": 1.0},
    },
}


class OneStepStabilizer:
    """Un único estado: prioriza movimientos que dejan bien puesto el contenedor movido.
    Si no hay ninguno, cede al comodín del framework."""

    states = ("stabilize",)

    def __init__(self, problem, good_move_bias: float = 25.0, sorted_destination_bias: float = 10.0, height_bias: float = 1.0):
        self.problem = problem
        self.good_move_bias = good_move_bias
        self.sorted_destination_bias = sorted_destination_bias
        self.height_bias = height_bias

    def initial(self, partial):
        return "stabilize", (partial.bad(),)

    def transition(self, partial, state, memory):
        if state != "stabilize":
            return FALLBACK, ()
        for so, s in enumerate(partial.stacks):
            if not s:
                continue
            c = s[-1]
            for sd in range(partial.S):
                if so == sd or len(partial.stacks[sd]) >= partial.H:
                    continue
                if c <= partial.g(sd):
                    return "stabilize", memory
        return FALLBACK, ()

    def score(self, partial, state, memory, action):
        if state != "stabilize":
            return 0.0
        so, sd = action.so, action.sd
        c = partial.stacks[so][-1]
        dest_sorted = 1 if partial.sorted_n[sd] == len(partial.stacks[sd]) else 0
        good = 1 if c <= partial.g(sd) else 0
        height_term = float(len(partial.stacks[sd]))
        return (
            -self.good_move_bias * good
            - self.sorted_destination_bias * dest_sorted * good
            + self.height_bias * height_term
            + (0.0 if good else 1.0)
        )

    def update(self, partial, state, memory, action):
        if state != "stabilize":
            return memory
        bad0 = memory[0] if memory else partial.bad()
        return (bad0,)


def build_component(problem, **params):
    return OneStepStabilizer(
        problem,
        good_move_bias=params.get("good_move_bias", 25.0),
        sorted_destination_bias=params.get("sorted_destination_bias", 10.0),
        height_bias=params.get("height_bias", 1.0),
    )
