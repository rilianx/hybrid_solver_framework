"""Muestreo de vecindarios: la parte del contrato que permite no recorrerlos completos.

`Neighborhood.moves(sol)` enumera; eso basta cuando `delta` es barato. Cuando cada
`delta` cuesta una evaluación cara (un LP en el CLSP), recorrer el vecindario entero
en cada paso de la búsqueda local se come el presupuesto, y cortar el recorrido por
tiempo es peor: el orden de `moves` es fijo, así que se evalúan siempre los mismos
primeros movimientos. Las runs 2 y 4 dejaron a ILS y VNS en ~40 % de gap por eso.

Los esqueletos piden movimientos a través de estas dos funciones y no de `moves`:

    random_move(nbh, sol, rng)        un movimiento al azar (SA, shake de VNS)
    sample_moves(nbh, sol, k, rng)    hasta k movimientos distintos al azar (LS, TS)

Un vecindario puede implementar `sample(sol, k, rng)` (`SampledNeighborhood`) cuando
sabe muestrear sin enumerar; si no, se enumera y se muestrea aquí. Así los componentes
que ya existen siguen funcionando sin cambios.
"""

from __future__ import annotations

from random import Random
from typing import Any, Protocol, runtime_checkable

from core.contracts import Move, Solution


@runtime_checkable
class SampledNeighborhood(Protocol):
    """Extensión OPCIONAL del slot `neighborhood`.

    `sample(sol, k, rng)` devuelve hasta `k` movimientos DISTINTOS de `moves(sol)`, elegidos
    al azar con `rng` (determinista dada la semilla). Menos de `k` solo si el vecindario
    tiene menos movimientos. Conviene cuando enumerar `moves(sol)` es caro por sí mismo.
    """

    def sample(self, sol: Solution, k: int, rng: Random) -> list[Move]: ...


def sample_moves(nbh: Any, sol: Solution, k: int | None, rng: Random) -> list[Move]:
    """Hasta `k` movimientos distintos elegidos al azar. Si el vecindario tiene `k` o menos,
    devuelve todos en el orden de `moves` sin gastar números aleatorios (igual que con
    `k=None`, el recorrido completo)."""
    if k is None:
        return list(nbh.moves(sol))
    sampler = getattr(nbh, "sample", None)
    if callable(sampler):
        return list(sampler(sol, k, rng))[:k]
    moves = list(nbh.moves(sol))
    return moves if len(moves) <= k else rng.sample(moves, k)


def random_move(nbh: Any, sol: Solution, rng: Random) -> Move | None:
    """Un movimiento al azar, o None si el vecindario está vacío."""
    sampler = getattr(nbh, "sample", None)
    if callable(sampler):
        got = list(sampler(sol, 1, rng))
        return got[0] if got else None
    moves = list(nbh.moves(sol))
    return rng.choice(moves) if moves else None


__all__ = ["SampledNeighborhood", "random_move", "sample_moves"]
