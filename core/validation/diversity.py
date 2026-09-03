"""Diversidad estructural entre componentes del mismo slot.

Motivo (corrida 5): al exigir que un vecindario mejore desde la solución de
partida, el modelo converge al único movimiento elemental que mejora — flips
de un setup — y los tres "vecindarios distintos" salieron con Jaccard 0,75–1,00
entre sí y con el escrito a mano. El gate estricto no enseña diversidad: la
embudona. Pedir diversidad *por nombre* (`avoid_names`) no alcanza; hay que
compararlos estructuralmente contra los ya aceptados.

Firma de un componente = lo que produce desde una solución fija, no su código.
Hay dos tipos de firma, y cada uno tiene su noción de similitud:

- **Conjuntos** (vecindario, perturbación): el conjunto de soluciones
  alcanzables. Similitud = Jaccard. Dos operadores con representaciones
  distintas del mismo movimiento dan el mismo conjunto, que es exactamente
  lo que queremos detectar.

- **Perfiles** (destrucción): comparar conjuntos exactos de `free_vars` NO
  sirve (corrida 6). Dos destrucciones aleatorias con la MISMA idea dan
  Jaccard 1,00 si comparten el estado del rng y 0,11 si no: el resultado mide
  la sincronía del rng, no la idea. Por eso una destrucción se resume en un
  perfil de descriptores *de forma* del conjunto liberado, promediados sobre
  muchas semillas — cuántos ejes toca, cuán concentrado está en un ítem o en
  un período, si los períodos son contiguos, si libera setups encendidos o
  apagados. `random_setups` y `period_window` liberan la misma cantidad de
  variables pero con formas muy distintas, y eso es lo que las distingue.
"""

from __future__ import annotations

import re
from collections import Counter
from random import Random
from statistics import mean
from typing import Any

_INT = re.compile(r"\d+")


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a | b) else 1.0


def profile_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """1.0 = perfiles idénticos; se queda con el descriptor que MÁS los separa.

    El promedio no sirve: la mayoría de los descriptores empata entre destrucciones
    distintas (liberan la misma cantidad de variables, casi todas encendidas) y diluye
    al uno o dos que capturan la idea. Medido sobre 6 destrucciones de la corrida 6,
    el promedio de diferencias relativas daba 0,77–0,92 para *todos* los pares —
    indistinguible del 1,00 de dos veces la misma idea — mientras el máximo separa
    limpio: 1,00 para la misma idea, ≤ 0,64 para ideas distintas.
    """
    keys = set(a) & set(b)
    if not keys:
        return 1.0
    return max(0.0, 1.0 - max(abs(a[k] - b[k]) / (a[k] + b[k] + 1e-9) for k in keys))


def similarity(sig_a, sig_b) -> float:
    if isinstance(sig_a, dict) and isinstance(sig_b, dict):
        return profile_similarity(sig_a, sig_b)
    if isinstance(sig_a, dict) or isinstance(sig_b, dict):
        return 0.0
    return jaccard(sig_a, sig_b)


def neighborhood_signature(impl, sol, problem=None, limit: int = 1000) -> set:
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


def perturbation_signature(impl, sol, problem=None, strength: float = 2.0, seeds=(0, 1, 2, 3, 4)) -> set:
    return {impl.perturb(sol, strength, Random(s)) for s in seeds}


# --------------------------------------------------------------------------- destrucción


def _coords(name: str) -> tuple[int, ...]:
    """Coordenadas de una variable a partir de su nombre (`y_3_11` -> (3, 11)).
    Genérico a propósito: no sabe de CLSP, solo de enteros en el nombre."""
    return tuple(int(x) for x in _INT.findall(name))


def _shape_features(free: list[str], total: int, assignment: dict | None) -> dict[str, float]:
    n = len(free)
    if n == 0:
        return {"size_ratio": 0.0}
    coords = [_coords(v) for v in free]
    n_axes = min((len(c) for c in coords), default=0)
    feats = {"size_ratio": min(1.0, n / max(1, total))}
    for axis in range(n_axes):
        counts = Counter(c[axis] for c in coords)
        vals = sorted(counts)
        feats[f"axis{axis}_concentration"] = max(counts.values()) / n  # 1.0 = todo en un solo valor
        feats[f"axis{axis}_spread"] = len(counts) / n  # 1.0 = un valor distinto por variable
        span = vals[-1] - vals[0] + 1
        feats[f"axis{axis}_contiguity"] = len(counts) / span if span else 1.0
    if assignment is not None:
        on = sum(1 for v in free if assignment.get(v, 0.0) > 0.5)
        feats["on_fraction"] = on / n
    return feats


def destruction_signature(
    impl, sol, problem=None, ratio: float = 0.3, seeds=tuple(range(20))
) -> dict[str, float]:
    """Perfil de forma del conjunto liberado, promediado sobre muchas semillas."""
    assignment = None
    total = 0
    if problem is not None:
        try:
            assignment = problem.to_assignment(sol)
            total = len(assignment)
        except Exception:  # noqa: BLE001
            assignment = None
    rows = []
    for s in seeds:
        _, free = impl.destroy(sol, ratio, Random(s))
        free = list(free)
        rows.append(_shape_features(free, total or max(1, len(free)), assignment))
    keys = set().union(*rows) if rows else set()
    return {k: mean(r.get(k, 0.0) for r in rows) for k in keys}


SIGNATURE = {
    "neighborhood": neighborhood_signature,
    "destruction": destruction_signature,
    "perturbation": perturbation_signature,
}


def signature(slot: str, impl, sol, problem=None):
    fn = SIGNATURE.get(slot)
    if fn is None:
        return None
    try:
        return fn(impl, sol, problem)
    except Exception:  # noqa: BLE001
        return None


def most_similar(slot: str, impl, peers: list[tuple[str, Any]], sol, problem=None) -> tuple[str, float] | None:
    """(nombre, similitud) del par ya aceptado más parecido, o None si no aplica."""
    mine = signature(slot, impl, sol, problem)
    if not mine:
        return None
    best = None
    for name, peer in peers:
        theirs = signature(slot, peer, sol, problem)
        if not theirs:
            continue
        j = similarity(mine, theirs)
        if best is None or j > best[1]:
            best = (name, j)
    return best
