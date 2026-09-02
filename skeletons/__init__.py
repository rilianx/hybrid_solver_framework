"""Especializaciones del esqueleto genérico (§5 de la propuesta).

Cada función `build_*` recibe el `ProblemModel` y los componentes que
ocupan cada slot, y retorna un `TrajectorySkeleton` ya configurado
(candidate_generator + state_updaters + estado inicial). El bucle de
`run()` es siempre el de `core.skeleton.TrajectorySkeleton`.
"""

from .sa import build_sa
from .ils import build_ils
from .lns_mip import build_lns_mip
from .relax_and_fix import RelaxAndFixConstructor
from .fix_and_optimize import build_fix_and_optimize

__all__ = ["build_sa", "build_ils", "build_lns_mip", "RelaxAndFixConstructor", "build_fix_and_optimize"]
