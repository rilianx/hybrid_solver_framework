from __future__ import annotations

from typing import Iterable, Tuple, Any
from examples.cvrp.problem_model import canonical

COMPONENT = {
    "name": "or_opt_block",
    "slot": "neighborhood",
    "compatible_skeletons": ["SA", "ILS", "TS", "VNS", "GRASP", "MIP_PERTURB"],
    "requires": ["ProblemModel.objective", "ProblemModel.inst"],
    "params": {
        "block_size": {"type": "int", "range": [2, 10]},
    },
}


class OrOptBlockNeighborhood:
    """Or-opt de bloque: mueve un bloque consecutivo de clientes dentro o entre rutas.

    Movimiento = (src_sig, dst_sig, i, j, k), donde:
      - src_sig es la firma (tupla) de la ruta origen,
      - dst_sig es la firma (tupla) de la ruta destino,
      - i, j delimitan el bloque r[i:j+1] a extraer en la ruta origen,
      - k es la posición de inserción en la ruta destino antes de eliminar el bloque.
    """

    def __init__(self, problem, block_size: int = 4):
        self.problem = problem
        self.block_size = block_size

    def _as_lists(self, sol):
        return [list(r) for r in sol]

    def _route_signature(self, r):
        return tuple(r)

    def _find_route_index(self, routes, sig):
        for idx, r in enumerate(routes):
            if tuple(r) == sig:
                return idx
        return None

    def moves(self, sol) -> Iterable[tuple]:
        routes = list(sol)
        for src in routes:
            L = len(src)
            if L == 0:
                continue
            src_sig = self._route_signature(src)
            max_len = min(self.block_size, L)
            for i in range(L):
                for j in range(i, min(L, i + max_len)):
                    block_len = j - i + 1
                    for dst in routes:
                        dst_sig = self._route_signature(dst)
                        D = len(dst)
                        if src_sig == dst_sig and L == 1:
                            continue
                        # Posiciones de inserción en la ruta destino (0..D)
                        for k in range(D + 1):
                            if src_sig == dst_sig:
                                # Evitar movimientos triviales: insertar el bloque en el mismo hueco
                                # o en una posición que no cambie la secuencia.
                                if k >= i and k <= j + 1:
                                    continue
                            yield (src_sig, dst_sig, i, j, k)

    def apply(self, sol, m):
        src_sig, dst_sig, i, j, k = m
        routes = self._as_lists(sol)

        src_idx = self._find_route_index(routes, src_sig)
        dst_idx = self._find_route_index(routes, dst_sig)
        if src_idx is None or dst_idx is None:
            return canonical(routes)

        src = routes[src_idx]
        dst = routes[dst_idx]

        if not (0 <= i <= j < len(src)):
            return canonical(routes)
        if not (0 <= k <= len(dst)):
            return canonical(routes)

        block = src[i : j + 1]

        # Quitar bloque de origen
        new_src = src[:i] + src[j + 1 :]

        # Ajustar inserción si origen y destino son la misma ruta
        if src_idx == dst_idx:
            base = new_src
            if k > i:
                k = k - len(block)
            if not (0 <= k <= len(base)):
                return canonical(routes)
            new_dst = base[:k] + block + base[k:]
            routes[src_idx] = new_dst
        else:
            if not (0 <= k <= len(dst)):
                return canonical(routes)
            new_dst = dst[:k] + block + dst[k:]
            routes[src_idx] = new_src
            routes[dst_idx] = new_dst

        routes = [r for r in routes if len(r) > 0]
        return canonical(routes)

    def undo(self, sol, m):
        src_sig, dst_sig, i, j, k = m
        routes = self._as_lists(sol)

        src_idx = self._find_route_index(routes, src_sig)
        dst_idx = self._find_route_index(routes, dst_sig)
        if src_idx is None or dst_idx is None:
            return canonical(routes)

        src = routes[src_idx]
        dst = routes[dst_idx]

        block_len = j - i + 1

        # Invertir la operación: retirar el bloque de la ruta destino y reinsertarlo en origen.
        if src_idx == dst_idx:
            # Misma ruta: recuperar el estado previo exactamente.
            # Para el undo, la secuencia final corresponde a mover el bloque desde posición k
            # de vuelta a i. Como el bloque se conserva, reconstruimos la ruta previa.
            if not (0 <= i <= j < len(src)):
                return canonical(routes)
            # Localizar el bloque en la solución actual usando k y el orden relativo.
            # Al ser movimiento reversible, basta reconstruir por extracción/inserción.
            # Primero, obtener una copia mutable.
            r = list(src)
            if not (0 <= k <= len(r)):
                return canonical(routes)

            # Determinar la posición actual del bloque: se reinsertó en k, por lo que
            # al deshacer lo extraemos de su posición actual.
            # La reconstrucción exacta se realiza retirando el bloque del lugar actual
            # y reinsertándolo en i.
            # Si k > i en el apply, el bloque fue insertado tras la extracción, así que
            # aquí la posición actual del bloque es k.
            current_start = k
            if k > i:
                current_start = k
            if current_start + block_len > len(r):
                return canonical(routes)

            block = r[current_start : current_start + block_len]
            without = r[:current_start] + r[current_start + block_len :]
            if not (0 <= i <= len(without)):
                return canonical(routes)
            restored = without[:i] + block + without[i:]
            routes[src_idx] = restored
        else:
            if not (0 <= i <= j < len(src)):
                return canonical(routes))
            # En el apply el bloque fue insertado en dst en la posición k.
            # Para deshacerlo, extraemos el mismo bloque desde dst y lo colocamos de vuelta en src.
            if not (0 <= k <= len(dst)):
                return canonical(routes)
            if k + block_len > len(dst):
                return canonical(routes)

            block = dst[k : k + block_len]
            new_dst = dst[:k] + dst[k + block_len :]

            # Reinsertar en el origen exactamente en i
            if not (0 <= i <= len(src)):
                return canonical(routes)
            new_src = src[:i] + block + src[i:]

            routes[src_idx] = new_src
            routes[dst_idx] = new_dst

        routes = [r for r in routes if len(r) > 0]
        return canonical(routes)

    def delta(self, sol, m):
        new_sol = self.apply(sol, m)
        return self.problem.objective(new_sol) - self.problem.objective(sol)


def build_component(problem, block_size: int = 4):
    return OrOptBlockNeighborhood(problem, block_size=block_size)
