COMPONENT = {'name': 'repair_sorted_prefix', 'slot': 'construction_machine', 'compatible_skeletons': ['CONSTRUCT'], 'requires': [], 'params': {'score_k1': {'type': 'float', 'range': [0.0, 20.0], 'default': 10.0}, 'score_k2': {'type': 'float', 'range': [0.0, 0.2], 'default': 0.1}}}
from core.machine import FALLBACK

class RepairSortedPrefix:
    _auto_score_k1 = 10.0
    _auto_score_k2 = 0.1
    'Estado de reparación: prioriza movimientos que reducen la cantidad de mal puestos y\n    favorecen la preservación/expansión de prefijos ordenados.'
    states = ('repair',)

    def __init__(self, problem):
        self.problem = problem

    def initial(self, partial):
        if partial.is_sorted():
            return (FALLBACK, ())
        return ('repair', (partial.bad(),))

    def transition(self, partial, state, memory):
        if partial.is_sorted():
            return (FALLBACK, ())
        return ('repair', memory)

    def score(self, partial, state, memory, action):
        sim = partial.copy(track=False)
        sim.move(action.so, action.sd)
        bad = sim.bad()
        ub_sum = sum((sim.ub(i) for i in range(sim.S)))
        disturb_sorted = 1 if partial.is_sorted_stack(action.so) else 0
        target_pressure = sim.h(action.sd)
        source_height = sim.h(action.so)
        return bad * 1000.0 + ub_sum * 100.0 + disturb_sorted * self._auto_score_k1 + target_pressure * 1.0 + source_height * self._auto_score_k2

    def update(self, partial, state, memory, action):
        return (partial.bad(),)

def _build_component_llm(problem):
    return RepairSortedPrefix(problem)

_MACHINE = RepairSortedPrefix
_AUTO = {'score_k1': 10.0, 'score_k2': 0.1}

def build_component(problem, **params):
    """Envoltura del framework: los números que el LLM dejó sueltos en los métodos son parámetros
    (`_AUTO`, declarados en COMPONENT); se fijan en la clase mientras se construye (por si
    `__init__` los usa) y en la instancia."""
    auto = {k: params.pop(k, v) for k, v in _AUTO.items()}
    saved = {k: getattr(_MACHINE, "_auto_" + k) for k in auto}
    for k, v in auto.items():
        setattr(_MACHINE, "_auto_" + k, v)
    try:
        obj = _build_component_llm(problem, **params)
    finally:
        for k, v in saved.items():
            setattr(_MACHINE, "_auto_" + k, v)
    for k, v in auto.items():
        setattr(obj, "_auto_" + k, v)
    return obj
