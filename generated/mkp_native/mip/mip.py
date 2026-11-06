import math

from examples.mkp.model_parts import canonical, wrap


def _name(j):
    return f"x_{j}"


def variables(inst):
    return {_name(j): (0.0, 1.0, "binary") for j in inst.items}


def structural_variables(inst):
    return [_name(j) for j in inst.items]


def to_assignment(inst, sol):
    sel = canonical(sol)[0]
    return {_name(j): float(sel[j]) for j in inst.items}


def aux_values(inst, sol):
    return {}


def from_assignment(inst, x):
    return wrap([1 if x.get(_name(j), 0.0) > 0.5 else 0 for j in inst.items])


def constraint_families(inst):
    rows = []
    for i in inst.resources:
        coefs = {_name(j): float(inst.weight[i][j]) for j in inst.items if inst.weight[i][j] != 0}
        rows.append((coefs, "<=", float(inst.capacity[i])))
    return {"capacidad": rows}


def objective_terms(inst):
    coefs = {_name(j): -float(inst.profit[j]) for j in inst.items}
    return {"beneficio": (coefs, 0.0)}


def _ratio(inst, j):
    use = sum(inst.weight[i][j] / inst.capacity[i] for i in inst.resources if inst.capacity[i] > 0)
    return inst.profit[j] / use if use > 0 else math.inf


def variable_groups(inst):
    n = inst.n_items
    if n == 0:
        return {}
    # Ítems de eficiencia similar compiten entre sí: bloques consecutivos según la razón greedy.
    order = sorted(inst.items, key=lambda j: (-_ratio(inst, j), j))
    size = max(1, min(n // 4, 10))
    groups = {}
    for g, start in enumerate(range(0, n, size)):
        groups[f"g{g}"] = [_name(j) for j in order[start:start + size]]
    return groups
