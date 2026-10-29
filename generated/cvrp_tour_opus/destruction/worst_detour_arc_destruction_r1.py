from random import Random

from generated.cvrp_tour_cycle.model.parts import canonical  # noqa: F401

COMPONENT = {
    "name": "worst_detour_arc_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "ratio": {"type": "float", "range": [0.05, 0.6]},
        "determinism": {"type": "float", "range": [1.0, 10.0]},
    },
}


def _neighbors(assignment, customers):
    succ = {}
    starts = []
    for name, v in assignment.items():
        if v > 0.5:
            _, a, b = name.split("_")
            a, b = int(a), int(b)
            if a == 0:
                starts.append(b)
            else:
                succ[a] = b
    pred, nxt, seen = {}, {}, set()
    for s in sorted(starts):
        prev, cur = 0, s
        while cur != 0 and cur not in seen:
            seen.add(cur)
            pred[cur] = prev
            nxt[cur] = succ.get(cur, 0)
            prev, cur = cur, succ.get(cur, 0)
    for c in customers:
        if c not in pred:
            pred[c], nxt[c] = 0, 0
    return pred, nxt


class WorstDetourArcDestruction:
    """Libera los clientes con mayor ahorro de eliminación d(p,c)+d(c,s)-d(p,s) (selección
    sesgada aleatoria), sus arcos incidentes y los arcos que permiten unir p y s directamente."""

    def __init__(self, problem, inst, determinism):
        self.problem, self.inst = problem, inst
        self.determinism = determinism

    def destroy(self, sol, ratio: float, rng: Random):
        inst = self.inst
        assignment = self.problem.to_assignment(sol)
        customers = list(inst.customers)
        n = len(customers)
        nn = inst.n_customers
        if n == 0:
            return {}, set()
        k = max(1, min(n, int(round(max(0.0, ratio) * n))))
        pred, nxt = _neighbors(assignment, customers)

        saving = {}
        for c in customers:
            p, s = pred[c], nxt[c]
            saving[c] = inst.dist(p, c) + inst.dist(c, s) - inst.dist(p, s) + rng.random() * 1e-9
        ranked = sorted(customers, key=lambda c: -saving[c])

        S = set()
        while len(S) < k and ranked:
            idx = int((rng.random() ** self.determinism) * len(ranked))
            idx = min(idx, len(ranked) - 1)
            S.add(ranked.pop(idx))

        A = set(S) | {0}
        for c in S:
            A.add(pred[c])
            A.add(nxt[c])

        free_vars = set()
        for i in range(nn + 1):
            for j in range(nn + 1):
                if i == j:
                    continue
                if i in S or j in S or (i in A and j in A):
                    name = f"x_{i}_{j}"
                    if name in assignment:
                        free_vars.add(name)
        if not free_vars:
            free_vars.add(next(iter(assignment)))
        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, determinism=3.0):
    return WorstDetourArcDestruction(problem, problem.inst, determinism)
