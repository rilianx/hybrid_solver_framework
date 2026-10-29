from random import Random

COMPONENT = {
    "name": "random_customer_arc_destruction",
    "slot": "destruction",
    "compatible_skeletons": ["LNS_MIP", "MIP_PERTURB"],
    "requires": ["ProblemModel.to_assignment"],
    "params": {
        "neighbor_prob": {"type": "float", "range": [0.0, 1.0]},
    },
}


class RandomCustomerArcDestruction:
    """Elige clientes al azar y libera todos los arcos x_i_j incidentes a ellos
    (y, con probabilidad neighbor_prob, también los de su predecesor/sucesor)."""

    def __init__(self, problem, inst, neighbor_prob):
        self.problem = problem
        self.inst = inst
        self.neighbor_prob = float(neighbor_prob)

    def _neighbors(self, sol):
        pred, succ = {}, {}
        for r in sol:
            nodes = [int(c) for c in r]
            for k, c in enumerate(nodes):
                pred[c] = nodes[k - 1] if k > 0 else 0
                succ[c] = nodes[k + 1] if k + 1 < len(nodes) else 0
        return pred, succ

    def _free_arcs(self, nodes, assignment):
        N = self.inst.n_customers + 1
        free = set()
        for t in nodes:
            for k in range(N):
                if k == t:
                    continue
                a = f"x_{t}_{k}"
                b = f"x_{k}_{t}"
                if a in assignment:
                    free.add(a)
                if b in assignment:
                    free.add(b)
        return free

    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        custs = list(self.inst.customers)
        n = len(custs)
        if n == 0 or not assignment:
            keys = sorted(assignment)
            free = {keys[0]} if keys else set()
            return {v: x for v, x in assignment.items() if v not in free}, free
        k = max(1, min(n, int(round(ratio * n))))
        chosen = set(rng.sample(custs, k))
        pred, succ = self._neighbors(sol)
        extra = set()
        for c in chosen:
            if rng.random() < self.neighbor_prob:
                p = pred.get(c, 0)
                s = succ.get(c, 0)
                if p != 0:
                    extra.add(p)
                if s != 0:
                    extra.add(s)
        nodes = chosen | extra
        free_vars = self._free_arcs(nodes, assignment)
        if not free_vars:
            free_vars = {sorted(assignment)[0]}
        partial = {v: x for v, x in assignment.items() if v not in free_vars}
        return partial, free_vars


def build_component(problem, neighbor_prob=0.5):
    return RandomCustomerArcDestruction(problem, problem.inst, neighbor_prob)
