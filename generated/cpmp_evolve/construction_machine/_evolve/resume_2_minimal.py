
COMPONENT = {"name": "minimal", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "requires": [],
             "params": {}}

from core.machine import FALLBACK


class Minimal:
    """Máquina mínima: sin estados propios todavía; cada paso lo decide el comodín del framework."""

    states = ()

    def __init__(self, problem):
        self.problem = problem

    def initial(self, partial):
        return FALLBACK, ()

    def transition(self, partial, state, memory):
        return FALLBACK, ()

    def score(self, partial, state, memory, action):
        return 0.0

    def update(self, partial, state, memory, action):
        return memory


def build_component(problem):
    return Minimal(problem)
