COMPONENT = {
    "name": "source_relief_and_space_score",
    "slot": "greedy_score",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "LNS_MIP", "FIX_OPT", "LOCAL_BRANCH", "MIP_PERTURB"],
    "requires": [],
    "params": {
        "relief_weight": {"type": "float", "range": [0.0, 3.0]},
        "space_weight": {"type": "float", "range": [0.0, 3.0]},
        "source_height_weight": {"type": "float", "range": [0.0, 2.0]},
    },
}


class SourceReliefAndSpaceScore:
    """CPMP: prioriza movimientos que liberen pilas problemáticas y utilicen espacio útil.

    Idea principal:
    - mover desde pilas altas/desordenadas da más "alivio";
    - preferir destinos con más holgura para no bloquear el sistema;
    - el criterio de desempate favorece vaciar arriba sin sobrecargar pilas ya densas.

    Menor puntaje = mejor acción.
    """

    def __init__(
        self,
        problem,
        relief_weight: float = 1.0,
        space_weight: float = 1.0,
        source_height_weight: float = 0.25,
    ):
        self.inst = problem.inst
        self.relief_weight = float(relief_weight)
        self.space_weight = float(space_weight)
        self.source_height_weight = float(source_height_weight)

    @staticmethod
    def _stack_violations(stack: tuple[int, ...]) -> int:
        return sum(1 for i in range(len(stack) - 1) if stack[i] < stack[i + 1])

    def score(self, partial, action) -> float:
        state = partial.state
        so, sd = int(action[0]), int(action[1])

        src = state[so]
        dst = state[sd]
        moving = src[-1]

        # Relieve del origen: cuanto más alto y desordenado esté el origen, mejor sacarle el tope.
        src_height = len(src)
        src_bad = self._stack_violations(src)

        # Holgura del destino.
        dst_slack = self.inst.H - len(dst)

        # Si el destino está vacío o su tope acepta bien al movedizo, mejor.
        if dst:
            top = dst[-1]
            compatibility = max(0, moving - top)  # 0 si apila "bien" o igual; peor si queda encima de uno menor.
        else:
            compatibility = 0.0

        # Favorece vaciar pilas altas y desordenadas.
        relief = src_bad + 1.0 / max(src_height, 1)

        # Castiga usar destinos con poca capacidad remanente.
        space_penalty = 1.0 / (1.0 + dst_slack)

        return (
            -self.relief_weight * relief
            + self.space_weight * space_penalty
            + self.source_height_weight * src_height
            + 0.1 * compatibility
        )


def build_component(
    problem,
    relief_weight: float = 1.0,
    space_weight: float = 1.0,
    source_height_weight: float = 0.25,
):
    return SourceReliefAndSpaceScore(
        problem,
        relief_weight=relief_weight,
        space_weight=space_weight,
        source_height_weight=source_height_weight,
    )
