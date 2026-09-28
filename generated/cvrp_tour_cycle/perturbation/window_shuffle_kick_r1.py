from random import Random

COMPONENT = {
    "name": "window_shuffle_kick",
    "slot": "perturbation",
    "compatible_skeletons": ["ILS"],
    "requires": [],
    "params": {"strength": {"type": "float", "range": [1.0, 10.0]}},
}


class WindowShuffleKick:
    def __init__(self, problem):
        self.problem = problem
        self.canonical = problem.parts.canonical

    def perturb(self, sol, strength: float, rng: Random):
        tour = list(self.canonical(sol))
        n = len(tour)
        if n <= 1:
            return self.canonical(tuple(tour))

        window = max(2, min(n, int(round(strength)) + 2))
        start = rng.randrange(0, n - window + 1) if window < n else 0
        end = start + window
        window_vals = tour[start:end]

        if len(window_vals) >= 2:
            rng.shuffle(window_vals)
        new_tour = tour[:start] + window_vals + tour[end:]

        if tuple(new_tour) == tuple(tour):
            # Guarantee a distinct perturbation by doing a cyclic shift of the window.
            if len(window_vals) >= 2:
                window_vals = window_vals[1:] + window_vals[:1]
                new_tour = tour[:start] + window_vals + tour[end:]
            else:
                i = rng.randrange(n)
                j = (i + 1) % n
                new_tour[i], new_tour[j] = new_tour[j], new_tour[i]

        return self.canonical(tuple(new_tour))


def build_component(problem, **params):
    _ = params.get("strength", 3.0)
    return WindowShuffleKick(problem)
