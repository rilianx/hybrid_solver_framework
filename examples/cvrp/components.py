"""Componentes del CVRP escritos a mano: el catálogo de referencia.

- `SingletonRoutes` (constructor): una ruta por cliente. Siempre factible y mala; es el
  equivalente del lot-for-lot del CLSP, la partida trivial.
- `RelocateNeighborhood`: mover un cliente a otra posición (de su ruta o de otra), o a una
  ruta nueva. Es el operador elemental del problema, como `setup_flip` en el CLSP.
- `TwoOptNeighborhood`: invertir un tramo de una ruta.
- `RelocateKick` (perturbación): `strength` movimientos de relocate al azar.
- `RandomRemoval` y `RadialRemoval` (destrucción): liberan los arcos alrededor de los
  clientes quitados para que el sub-MIP los reinserte.

Los movimientos se describen por clientes y no por índices de ruta, porque la forma
canónica reordena las rutas: `(c, pred, succ, nuevo_pred, nuevo_succ)`, con 0 = depósito.
"""

from __future__ import annotations

from random import Random

from .problem_model import CVRPModel, canonical, route_load, var_name


def _locate(sol, c):
    for k, r in enumerate(sol):
        if c in r:
            return k, r.index(c)
    raise ValueError(f"cliente {c} no está en la solución")


def _neighbors(route, pos):
    return (route[pos - 1] if pos > 0 else 0), (route[pos + 1] if pos + 1 < len(route) else 0)


def _insert(routes, c, pred, succ):
    """Inserta `c` entre `pred` y `succ` (0 = depósito; ambos 0 = ruta nueva)."""
    if pred != 0:
        k, i = _locate(routes, pred)
        routes[k].insert(i + 1, c)
    elif succ != 0:
        k, i = _locate(routes, succ)
        routes[k].insert(i, c)
    else:
        routes.append([c])


def _relocate(sol, c, pred, succ):
    routes = [list(r) for r in sol]
    k, i = _locate(routes, c)
    del routes[k][i]
    _insert(routes, c, pred, succ)
    return canonical(routes)


class SingletonRoutes:
    def build(self, inst, rng: Random):
        return canonical([(c,) for c in inst.customers])


class RelocateNeighborhood:
    """Mover un cliente entre dos nodos consecutivos de cualquier ruta, o a una ruta nueva.
    Solo destinos donde cabe su demanda."""

    def __init__(self, problem: CVRPModel):
        self.problem, self.inst = problem, problem.inst

    def moves(self, sol):
        inst = self.inst
        loads = [route_load(inst, r) for r in sol]
        for k, r in enumerate(sol):
            for i, c in enumerate(r):
                pred, succ = _neighbors(r, i)
                d = inst.demand[c]
                for k2, r2 in enumerate(sol):
                    if k2 != k and loads[k2] + d > inst.capacity + 1e-9:
                        continue
                    nodes = (0, *r2, 0)
                    for a, b in zip(nodes, nodes[1:]):
                        if c in (a, b) or (k2 == k and (a, b) == (pred, succ)):
                            continue
                        if k2 == k and a == 0 and b == 0:
                            continue
                        yield (c, pred, succ, a, b)
                if len(r) > 1:
                    yield (c, pred, succ, 0, 0)

    def apply(self, sol, m):
        c, _, _, a, b = m
        return _relocate(sol, c, a, b)

    def undo(self, sol, m):
        c, pred, succ, _, _ = m
        return _relocate(sol, c, pred, succ)

    def delta(self, sol, m):
        return self.problem.objective(self.apply(sol, m)) - self.problem.objective(sol) \
            if not self.problem.is_feasible(sol) else self._fast_delta(m)

    def _fast_delta(self, m):
        c, pred, succ, a, b = m
        d = self.inst.dist
        return (d(a, c) + d(c, b) - d(a, b)) - (d(pred, c) + d(c, succ) - d(pred, succ))


class TwoOptNeighborhood:
    """Invertir el tramo de una ruta entre los clientes `a` y `b` (a antes que b). El
    movimiento `(a, b)` se deshace con `(b, a)`."""

    def __init__(self, problem: CVRPModel):
        self.problem, self.inst = problem, problem.inst

    def moves(self, sol):
        for r in sol:
            for i in range(len(r)):
                for j in range(i + 1, len(r)):
                    yield (r[i], r[j])

    def apply(self, sol, m):
        a, b = m
        routes = [list(r) for r in sol]
        k, i = _locate(routes, a)
        j = routes[k].index(b)
        routes[k][i:j + 1] = reversed(routes[k][i:j + 1])
        return canonical(routes)

    def undo(self, sol, m):
        a, b = m
        return self.apply(sol, (b, a))

    def delta(self, sol, m):
        a, b = m
        k, i = _locate(sol, a)
        r = sol[k]
        j = r.index(b)
        prev = r[i - 1] if i > 0 else 0
        nxt = r[j + 1] if j + 1 < len(r) else 0
        d = self.inst.dist
        return d(prev, b) + d(a, nxt) - d(prev, a) - d(b, nxt)


class RelocateKick:
    """Perturbación: `strength` relocates al azar (sin mirar la distancia)."""

    def __init__(self, problem: CVRPModel):
        self.nbh = RelocateNeighborhood(problem)

    def perturb(self, sol, strength, rng: Random):
        for _ in range(max(1, int(round(strength)))):
            moves = list(self.nbh.moves(sol))
            if not moves:
                break
            sol = self.nbh.apply(sol, rng.choice(moves))
        return sol


def _free_arcs_around(problem: CVRPModel, sol, removed: set[int]):
    """Arcos entre los clientes quitados, sus vecinos de ruta y el depósito: el sub-MIP puede
    reinsertar a los quitados en cualquiera de esos huecos y cerrar los que dejan."""
    touched = set(removed)
    for r in sol:
        for i, c in enumerate(r):
            if c in removed:
                touched.update(_neighbors(r, i))
    touched.add(0)
    free = {var_name(i, j) for i in touched for j in touched if i != j}
    assignment = problem.to_assignment(sol)
    partial = {v: val for v, val in assignment.items() if v not in free}
    return partial, free


class RandomRemoval:
    def __init__(self, problem: CVRPModel):
        self.problem = problem

    def destroy(self, sol, ratio, rng: Random):
        custs = list(self.problem.inst.customers)
        k = max(1, int(round(ratio * len(custs))))
        return _free_arcs_around(self.problem, sol, set(rng.sample(custs, k)))


class RadialRemoval:
    """Quita al cliente semilla y a sus vecinos más cercanos (destrucción espacial)."""

    def __init__(self, problem: CVRPModel):
        self.problem = problem

    def destroy(self, sol, ratio, rng: Random):
        inst = self.problem.inst
        custs = list(inst.customers)
        k = max(1, int(round(ratio * len(custs))))
        seed = rng.choice(custs)
        near = sorted(custs, key=lambda c: inst.dist(seed, c))[:k]
        return _free_arcs_around(self.problem, sol, set(near))
