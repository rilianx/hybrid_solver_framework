"""`ProblemModel` del CPMP. La solución es la secuencia de movimientos (so, sd); es factible
si cada movimiento es válido (origen con contenedores, destino con espacio) y el layout
final está ordenado. Objetivo: cantidad de movimientos.

Por ahora el CPMP entra al framework solo por el lado constructivo (`construction_view`:
FRG, greedy con puntaje y beam search). No tiene vista MIP: `build_mip`, `to_assignment`,
`from_assignment` y `variable_groups` avisan con `NotImplementedError`, así que los
esqueletos matheurísticos no aplican todavía.
"""

from __future__ import annotations

from dataclasses import dataclass

from .construction import CPMPConstructionView
from .frg import Layout
from .instance import CPMPInstance


@dataclass(frozen=True)
class CPMPSolution:
    moves: tuple[tuple[int, int], ...]


class CPMPModel:
    def __init__(self, inst: CPMPInstance, **view_params):
        self.inst = inst
        self.view_params = view_params

    def load(self, path: str) -> CPMPInstance:
        return CPMPInstance.load(path)

    def replay(self, sol: CPMPSolution) -> Layout | None:
        L = Layout.from_instance(self.inst)
        try:
            for so, sd in sol.moves:
                L.move(so, sd)
        except (ValueError, IndexError):
            return None
        return L

    def is_feasible(self, sol: CPMPSolution) -> bool:
        L = self.replay(sol)
        return L is not None and L.is_sorted()

    def objective(self, sol: CPMPSolution) -> float:
        return float(len(sol.moves))

    def explain_infeasibility(self, sol: CPMPSolution) -> str:
        L = self.replay(sol)
        if L is None:
            return "la secuencia tiene un movimiento inválido (origen vacío, destino lleno u origen = destino)"
        bad = [i for i in range(L.S) if not L.is_sorted_stack(i)]
        return f"el layout final no está ordenado: pilas {bad} con {L.bad()} contenedores mal puestos"

    def construction_view(self, inst: CPMPInstance, **params) -> CPMPConstructionView:
        return CPMPConstructionView(self, inst, **{**self.view_params, **params})

    def build_mip(self, inst):
        raise NotImplementedError("CPMP: todavía sin vista MIP")

    def to_assignment(self, sol):
        raise NotImplementedError("CPMP: todavía sin vista MIP")

    def from_assignment(self, x):
        raise NotImplementedError("CPMP: todavía sin vista MIP")

    def variable_groups(self, inst):
        raise NotImplementedError("CPMP: todavía sin vista MIP")


__all__ = ["CPMPModel", "CPMPSolution"]
