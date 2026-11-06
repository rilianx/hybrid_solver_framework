import math

from examples.mkp.model_parts import canonical


def _x(j: int) -> str:
    return f"x_{j}"


def variables(inst) -> dict[str, tuple[float, float, str]]:
    return {_x(j): (0.0, 1.0, "binary") for j in inst.items}


def structural_variables(inst) -> list[str]:
    return [_x(j) for j in inst.items]


def to_assignment(inst, sol) -> dict[str, float]:
    s = canonical(sol)[0]
    return {_x(j): float(s[j]) for j in inst.items}


def aux_values(inst, sol) -> dict[str, float]:
    return {}


def from_assignment(inst, x) -> tuple:
    return canonical([[1 if float(x.get(_x(j), 0.0)) > 0.5 else 0 for j in inst.items]])


def constraint_families(inst) -> dict[str, list[tuple[dict[str, float], str, float]]]:
    rows = []
    for i in inst.resources:
        coefs = {_x(j): float(inst.weight[i][j]) for j in inst.items if inst.weight[i][j] != 0}
        rows.append((coefs, "<=", float(inst.capacity[i])))
    return {"capacidad": rows}


def objective_terms(inst) -> dict[str, tuple[dict[str, float], float]]:
    return {"beneficio": ({_x(j): -float(inst.profit[j]) for j in inst.items}, 0.0)}


def _ratio(inst, j):
    use = sum(inst.weight[i][j] / inst.capacity[i] for i in inst.resources if inst.capacity[i] > 0)
    return inst.profit[j] / use if use > 0 else float("inf")


def variable_groups(inst) -> dict[str, list[str]]:
    n = inst.n_items
    if n == 0:
        return {}
    order = sorted(inst.items, key=lambda j: (-_ratio(inst, j), j))
    g = min(n, max(4, math.ceil(n / 10)))
    while g < n and math.ceil(n / g) > n / 3:
        g += 1
    base, extra = divmod(n, g)
    groups = {}
    pos = 0
    for k in range(g):
        size = base + (1 if k < extra else 0)
        groups[f"g{k}"] = [_x(j) for j in order[pos:pos + size]]
        pos += size
    return groups
