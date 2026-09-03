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
from .ts import build_ts, TabuMemory
from .vns import build_vns
from .grasp import build_grasp
from .local_branching import build_local_branching

__all__ = [
    "build_sa", "build_ils", "build_lns_mip", "RelaxAndFixConstructor", "build_fix_and_optimize",
    "build_ts", "TabuMemory", "build_vns", "build_grasp", "build_local_branching",
]
