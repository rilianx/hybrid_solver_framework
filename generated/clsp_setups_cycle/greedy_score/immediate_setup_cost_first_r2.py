COMPONENT = {
    "name": "immediate_setup_cost_first",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "true_bias": {"type": "float", "range": [0.0, 10.0]},
        "false_bias": {"type": "float", "range": [-10.0, 10.0]},
        "setup_cost_weight": {"type": "float", "range": [0.0, 10.0]},
    },
}


class ImmediateSetupCostFirst:
    """Greedy constructivo para CLSP.
    Idea: prioriza decisiones que evitan abrir setups caros cuanto antes.
    Para una acción True penaliza el costo fijo del setup; para False da una
    pequeña ventaja para cerrar el período/ítem sin abrirlo.
    Menor score = mejor."""

    def __init__(self, problem, true_bias: float = 1.0, false_bias: float = -0.2, setup_cost_weight: float = 1.0):
        inst = problem.inst
        self.inst = inst
        self.true_bias = true_bias
        self.false_bias = false_bias
        self.setup_cost_weight = setup_cost_weight

        # Precalculo ligero: evitar accesos repetidos a atributos y conversiones a float
        # en cada llamada a score(), que se ejecuta cientos de miles de veces.
        self._setup_cost = tuple(float(c) for c in inst.setup_cost)
        self._base_score = tuple(self.setup_cost_weight * c for c in self._setup_cost)

    def score(self, partial, action) -> float:
        i, _t, val = action
        return self._base_score[i] + (self.true_bias if val else self.false_bias)


def build_component(problem, true_bias: float = 1.0, false_bias: float = -0.2, setup_cost_weight: float = 1.0):
    return ImmediateSetupCostFirst(problem, true_bias=true_bias, false_bias=false_bias, setup_cost_weight=setup_cost_weight)
