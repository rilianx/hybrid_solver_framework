"""Relax-and-Fix (§5.2/§5.3): un *constructor* matheurístico.

    groups ← P.variable_groups(inst); fixed ← {}
    para (fix_set, int_set, relax_set) en POLITICA.schedule(groups):
        x ← solve(model, fijar fixed, enteras int_set, relajar relax_set)
        si x es None: fallar (o backtrack)
        fixed ← fixed ∪ {v: x[v] para v en int_set que salen de la ventana}
    retornar P.from_assignment(fixed)

Como produce soluciones, implementa el `Protocol` `Constructor`
(`build(inst, rng)`), y por tanto puede ocupar el slot `constructor`
de *cualquier* otro esqueleto: Relax-and-Fix → SA, Relax-and-Fix →
Fix-and-Optimize, etc., sin plantillas nuevas (observación de §5.2).
"""

from __future__ import annotations

from random import Random

from core.contracts import FixingPolicy, ProblemModel


class RelaxAndFixConstructor:
    def __init__(
        self,
        problem: ProblemModel,
        fixing_policy: FixingPolicy,
        time_limit_per_window: float = 5.0,
        fallback=None,
    ) -> None:
        """`fallback`: Constructor alternativo si alguna ventana resulta infactible."""
        self.problem = problem
        self.fixing_policy = fixing_policy
        self.time_limit_per_window = time_limit_per_window
        self.fallback = fallback
        self.last_failed_window: int | None = None

    def build(self, inst, rng: Random):
        model = self.problem.build_mip(inst)
        groups = self.problem.variable_groups(inst)
        fixed: dict[str, float] = {}
        last_x: dict[str, float] | None = None
        self.last_failed_window = None

        for k, (fix_set, int_set, relax_set) in enumerate(self.fixing_policy.schedule(groups)):
            x = model.solve(
                fixed={v: fixed[v] for v in fix_set},
                integer=int_set,
                relaxed=relax_set,
                time_limit=self.time_limit_per_window,
                warm_start=last_x,
            )
            if x is None:
                self.last_failed_window = k
                if self.fallback is None:
                    raise RuntimeError(f"Relax-and-Fix: ventana {k} infactible y sin fallback")
                return self.fallback.build(inst, rng)
            last_x = x
            # Todo lo entero hasta ahora queda fijado; la política decide
            # (vía el fix_set de la siguiente ventana) qué se mantiene fijo.
            for v in int_set:
                fixed[v] = x[v]

        assert last_x is not None, "variable_groups vacío"
        return self.problem.from_assignment(last_x)
