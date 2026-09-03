"""Interfaz mínima que el núcleo exige a un "modelo MIP" (§3, §5.2).

`ProblemModel.build_mip(inst)` devuelve algo que cumple `MIPModel`. Las
matheurísticas (Relax-and-Fix, Fix-and-Optimize, LNS-MIP) solo hablan
con el modelo a través de `solve(...)`, indicando qué variables van
fijas, cuáles se mantienen enteras y cuáles se relajan. Así las
políticas de fijación no saben nada del problema concreto ni del
solver (PuLP/CBC, HiGHS, OR-Tools...).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class MIPModel(Protocol):
    # Valor objetivo del último `solve` exitoso (None si falló / aún no se llamó).
    # Lo usa la capa semántica de validación (§7) para comparar el objetivo del
    # MIP con el de la vista heurística sobre la misma solución.
    last_objective: float | None

    def variables(self) -> list[str]:
        """Nombres de las variables enteras/binarias sujetas a fijación/relajación."""
        ...

    def solve(
        self,
        fixed: dict[str, float],
        integer: set[str],
        relaxed: set[str],
        time_limit: float,
        warm_start: dict[str, float] | None = None,
        near: tuple[dict[str, float], int] | None = None,
    ) -> dict[str, float] | None:
        """Resuelve con `fixed` fijadas, `integer` enteras y `relaxed` continuas.

        `near=(x̄, k)` agrega la restricción de Local Branching (§5.2):
        distancia de Hamming a x̄ sobre las variables enteras ≤ k, es decir
        Σ_{x̄_j=0} x_j + Σ_{x̄_j=1} (1 − x_j) ≤ k.

        Toda variable de `variables()` debe caer en exactamente uno de los
        tres conjuntos. Devuelve la asignación de *todas* las variables de
        `variables()` (redondeadas donde eran enteras), o None si es
        infactible o no se encontró solución en `time_limit`.
        """
        ...
