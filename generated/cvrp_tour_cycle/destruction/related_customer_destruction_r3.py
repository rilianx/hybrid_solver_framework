    def destroy(self, sol, ratio: float, rng: Random):
        assignment = self.problem.to_assignment(sol)
        customers = list(getattr(self.inst, "customers", ()))
        if not customers:
            return dict(assignment), set()

        seed = rng.choice(customers)

        def demand(c):
            for attr in ("demand", "demands", "q", "service", "load"):
                if hasattr(self.inst, attr):
                    val = getattr(self.inst, attr)
                    try:
                        return float(val[c])
                    except Exception:
                        pass
            return 0.0

        seed_demand = demand(seed)

        def demand_gap(c):
            return abs(demand(c) - seed_demand)

        # Distinctive destruction: relatedness by demand similarity, not by contiguity.
        ordered = sorted((c for c in customers if c != seed), key=demand_gap)

        n = len(customers)
        k = max(1, min(n, int(round(ratio * n))))
        target_customers = {seed}
        for c in ordered:
            if len(target_customers) >= k:
                break
            target_customers.add(c)

        def mentions_customer(var_name, c):
            if not isinstance(var_name, str):
                return False
            parts = var_name.split("_")
            sc = str(c)
            return sc in parts

        free_vars = set()
        for v in assignment:
            if any(mentions_customer(v, c) for c in target_customers):
                free_vars.add(v)

        if not free_vars and assignment:
            free_vars.add(rng.choice(list(assignment.keys())))

        partial = {v: val for v, val in assignment.items() if v not in free_vars}
        return partial, free_vars
