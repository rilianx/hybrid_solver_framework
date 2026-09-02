"""Políticas de fijación genéricas (slot `fixing_policy`, §4/§5.2).

Trabajan solo sobre `variable_groups` (dict grupo -> variables), sin
conocer el problema: para lot sizing los grupos son períodos, para
ruteo podrían ser clusters de clientes, para scheduling máquinas.

- `SlidingWindowPolicy.schedule`: agenda de Relax-and-Fix. Recorre los
  grupos en orden; en cada paso los anteriores están fijos, la ventana
  actual es entera y el resto relajado. Con `overlap > 0` los últimos
  grupos de la ventana no se fijan al avanzar (se reoptimizan).
- `blocks`: partición de los grupos en bloques consecutivos de tamaño
  `block_size`, usada por Fix-and-Optimize para elegir qué liberar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator

Schedule = tuple[set[str], set[str], set[str]]  # (fix_set, integer_set, relax_set)


@dataclass
class SlidingWindowPolicy:
    window_size: int = 2
    overlap: int = 0

    def __post_init__(self) -> None:
        if self.window_size < 1:
            raise ValueError("window_size debe ser >= 1")
        if not 0 <= self.overlap < self.window_size:
            raise ValueError("overlap debe cumplir 0 <= overlap < window_size")

    def schedule(self, groups: dict[str, list[str]], params=None) -> Iterator[Schedule]:
        names = list(groups)
        all_vars = {v for g in names for v in groups[g]}
        step = self.window_size - self.overlap
        start = 0
        fixed_groups: list[str] = []
        while start < len(names):
            window = names[start : start + self.window_size]
            fix_set = {v for g in fixed_groups for v in groups[g]}
            int_set = {v for g in window for v in groups[g]}
            relax_set = all_vars - fix_set - int_set
            yield fix_set, int_set, relax_set
            if start + self.window_size >= len(names):
                break  # la ventana ya alcanzó el último grupo
            # al avanzar, se fijan los grupos de la ventana que salen de ella
            fixed_groups.extend(window[:step])
            start += step

    def blocks(self, groups: dict[str, list[str]], block_size: int) -> list[set[str]]:
        return consecutive_blocks(groups, block_size)


def consecutive_blocks(groups: dict[str, list[str]], block_size: int) -> list[set[str]]:
    if block_size < 1:
        raise ValueError("block_size debe ser >= 1")
    names = list(groups)
    return [
        {v for g in names[i : i + block_size] for v in groups[g]}
        for i in range(0, len(names), block_size)
    ]


def covers_all_variables(schedule: Iterable[Schedule], all_vars: set[str]) -> bool:
    """Propiedad verificable del slot (§4): la unión de los `integer_set` cubre todo."""
    seen: set[str] = set()
    for _fix, int_set, _relax in schedule:
        seen |= int_set
    return seen == all_vars
