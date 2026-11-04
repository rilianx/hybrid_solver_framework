"""Especializaciones del esqueleto genérico (§5 de la propuesta).

Cada función `build_*` recibe el `ProblemModel` y los componentes que
ocupan cada slot, y retorna un `TrajectorySkeleton` ya configurado
(candidate_generator + state_updaters + estado inicial). El bucle de
`run()` es siempre el de `core.skeleton.TrajectorySkeleton`.
"""

from .sa import build_sa
from .ils import build_ils
from .ts import build_ts, TabuMemory
from .vns import build_vns

__all__ = ["build_sa", "build_ils", "build_ts", "TabuMemory", "build_vns"]
