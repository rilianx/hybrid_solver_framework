COMPONENT = {
    "name": "misplacement_reduction_score",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "lookahead_weight": {"type": "float", "range": [0.0, 3.0]},
        "balance_weight": {"type": "float", "range": [0.0, 2.0]},
    },
}


class MisplacementReductionScore:
    """CPMP: puntúa por la reducción inmediata del desorden local.

    Idea principal:
    - prioriza acciones que reduzcan el número de ascensos bottom-up en la pila origen;
    - desempata favoreciendo destinos más "compatibles" y una distribución menos desequilibrada.

    Menor puntaje = mejor acción.
    """

    def __init__(self, problem, lookahead_weight: float = 1.0, balance_weight: float = 0.25):
        self.inst = problem.inst
        self.lookahead_weight = float(lookahead_weight)
        self.balance_weight = float(balance_weight)

    @staticmethod
    def _misplaced_in_stack(stack: tuple[int, ...]) -> int:
        return sum(1 for i in range(len(stack) - 1) if stack[i] < stack[i + 1])

    @staticmethod
    def _stack_slack(height: int, H: int) -> int:
        return H - height

    def score(self, partial, action) -> float:
        state = partial.state
        so, sd = int(action[0]), int(action[1])

        src = state[so]
        dst = state[sd]
        moving = src[-1]

        src_bad_before = self._misplaced_in_stack(src)
        dst_bad_before = self._misplaced_in_stack(dst)
        src_len = len(src)
        dst_len = len(dst)

        # Simulación local barata de la acción.
        new_src = src[:-1]
        new_dst = dst + (moving,)

        src_bad_after = self._misplaced_in_stack(new_src)
        dst_bad_after = self._misplaced_in_stack(new_dst)

        # Reducción del desorden: si mejora, baja el puntaje.
        delta_bad = (src_bad_after + dst_bad_after) - (src_bad_before + dst_bad_before)

        # Preferimos dejar más holgura y equilibrar alturas.
        new_heights = [len(st) for st in state]
        new_heights[so] -= 1
        new_heights[sd] += 1
        imbalance = max(new_heights) - min(new_heights)

        # Pequeña penalización por mover a una pila muy cargada.
        dst_fill = dst_len / max(self.inst.H, 1)

        return (
            float(delta_bad)
            + self.lookahead_weight * (1.0 if new_dst and new_dst[-2] < new_dst[-1] if len(new_dst) >= 2 else 0.0)
            + self.balance_weight * imbalance
            + 0.1 * dst_fill
        )


def build_component(problem, lookahead_weight: float = 1.0, balance_weight: float = 0.25):
    return MisplacementReductionScore(problem, lookahead_weight=lookahead_weight, balance_weight=balance_weight)
