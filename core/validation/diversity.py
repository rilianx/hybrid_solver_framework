"""Diversidad estructural entre componentes del mismo slot.

Motivo (corrida 5): al exigir que un vecindario mejore desde la solución de
partida, el modelo converge al único movimiento elemental que mejora — flips
de un setup — y los tres "vecindarios distintos" salieron con Jaccard 0,75–1,00
entre sí y con el escrito a mano. El gate estricto no enseña diversidad: la
embudona. Pedir diversidad *por nombre* (`avoid_names`) no alcanza; hay que
compararlos estructuralmente contra los ya aceptados.

Firma de un componente = el conjunto de resultados observables que produce
desde una solución fija, no su código:

- vecindario: conjunto de soluciones vecinas alcanzables desde `sol`.
- destrucción: conjuntos de `free_vars` liberados con semillas fijas.
- perturbación: soluciones producidas con semillas fijas.
"""

from __future__ import annotations

from random import Random
from typing import Any


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a | b) else 1.0


def neighborhood_signature(impl, sol, limit: int = 400) -> set:
    """Vecinos alcanzables desde `sol` (no los movimientos: dos operadores con
    representaciones distintas del mismo movimiento son el mismo vecindario)."""
    out = set()
    for k, m in enumerate(impl.moves(sol)):
        if k >= limit:
            break
        try:
            out.add(impl.apply(sol, m))
        except Exception:  # noqa: BLE001
            continue
    return out


def destruction_signature(impl, sol, ratio: float = 0.3, seeds=(0, 1, 2, 3, 4)) -> set:
    return {frozenset(impl.destroy(sol, ratio, Random(s))[1]) for s in seeds}


def perturbation_signature(impl, sol, strength: float = 2.0, seeds=(0, 1, 2, 3, 4)) -> set:
    return {impl.perturb(sol, strength, Random(s)) for s in seeds}


SIGNATURE = {
    "neighborhood": neighborhood_signature,
    "destruction": destruction_signature,
    "perturbation": perturbation_signature,
}


def signature(slot: str, impl, sol) -> set | None:
    fn = SIGNATURE.get(slot)
    if fn is None:
        return None
    try:
        return fn(impl, sol)
    except Exception:  # noqa: BLE001
        return None


def most_similar(slot: str, impl, peers: list[tuple[str, Any]], sol) -> tuple[str, float] | None:
    """(nombre, Jaccard) del par ya aceptado más parecido, o None si no aplica."""
    mine = signature(slot, impl, sol)
    if not mine:
        return None
    best = None
    for name, peer in peers:
        theirs = signature(slot, peer, sol)
        if not theirs:
            continue
        j = jaccard(mine, theirs)
        if best is None or j > best[1]:
            best = (name, j)
    return best
