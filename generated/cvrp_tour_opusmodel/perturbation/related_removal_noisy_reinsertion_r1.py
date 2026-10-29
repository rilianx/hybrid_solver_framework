from random import Random

from generated.cvrp_tour_opusmodel.model.parts import canonical

COMPONENT = {
    "name": "related_removal_noisy_reinsertion",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {
        "noise": {"type": "float", "range": [0.0, 1.0]},
        "max_fraction": {"type": "float", "range": [0.05, 0.5]},
    },
}


class RelatedRemovalNoisyReinsertion:
    def __init__(self, problem, noise=0.3, max_fraction=0.3):
        self.problem = problem
        self.inst = problem.inst
        self.noise = float(noise)
        self.max_fraction = float(max_fraction)

    def _ins_cost(self, tour, pos, c):
        dist = self.inst.dist
        prev = tour[pos - 1] if pos > 0 else 0
        nxt = tour[pos] if pos < len(tour) else 0
        return dist(prev, c) + dist(c, nxt) - dist(prev, nxt)

    def perturb(self, sol, strength: float, rng: Random):
        base = list(canonical(sol))
        n = len(base)
        if n < 2:
            return canonical(base)
        dist = self.inst.dist
        cap_k = max(1, int(self.max_fraction * n))
        k = max(1, min(int(round(strength)), cap_k, n - 1))
        seed = rng.choice(base)
        scored = sorted(
            base,
            key=lambda c: (dist(seed, c) * (1.0 + self.noise * rng.random()), c),
        )
        removed = scored[:k]
        rem_set = set(removed)
        tour = [c for c in base if c not in rem_set]
        rng.shuffle(removed)
        for c in removed:
            best_pos, best_val = 0, float("inf")
            for pos in range(len(tour) + 1):
                val = self._ins_cost(tour, pos, c) * (1.0 + self.noise * rng.random())
                if val < best_val:
                    best_val, best_pos = val, pos
            tour.insert(best_pos, c)
        if tour == base:
            i, j = rng.sample(range(n), 2)
            tour = list(base)
            tour[i], tour[j] = tour[j], tour[i]
        return canonical(tour)


def build_component(problem, noise=0.3, max_fraction=0.3):
    return RelatedRemovalNoisyReinsertion(problem, noise=noise, max_fraction=max_fraction)
