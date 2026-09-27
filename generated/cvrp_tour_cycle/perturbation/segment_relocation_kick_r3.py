def perturb(self, sol, strength: float, rng: Random):
    tour = list(self.canonical(sol))
    n = len(tour)
    if n < 2:
        return self.canonical(tuple(tour))

    # More strength => more elementary relocations, hence larger disruption.
    steps = max(1, min(n - 1, int(round(strength))))
    for _ in range(steps):
        if len(tour) < 2:
            break
        i = rng.randint(0, len(tour) - 1)
        customer = tour.pop(i)
        insert_pos = rng.randint(0, len(tour))
        if insert_pos == i:
            insert_pos = (insert_pos + 1) % (len(tour) + 1)
        tour.insert(insert_pos, customer)

    if tuple(tour) == tuple(self.canonical(sol)) and n >= 2:
        # Guaranteed change with a single relocation.
        i = rng.randint(0, n - 1)
        customer = tour.pop(i)
        insert_pos = rng.randint(0, n - 1)
        if insert_pos >= i:
            insert_pos += 1
        tour.insert(insert_pos, customer)

    return self.canonical(tuple(tour))
