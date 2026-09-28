"""Layout del CPMP: pilas, movimientos y consultas del problema. Neutral: no sabe nada de
ninguna heurística (FRG vive en `frg.py`, como un componente más del catálogo).

Es el estado parcial de la vista constructiva: un puntaje (slot `greedy_score`) lo lee para
decidir, así que todo lo que expone es semántica del problema (bien/mal puesto, huecos,
grupo del tope, contenedores desbloqueados), no reglas de decisión.
"""

from __future__ import annotations

from .instance import CPMPInstance


class Layout:
    """Layout mutable. `copy()` antes de modificarlo si es un parcial de la vista.

    Atributos: stacks (listas de grupos, abajo → arriba), H (altura máxima), G (grupo
    máximo), S, N, moves (lista de (so, sd) hechos desde el layout inicial), sorted_n[i]
    (contenedores bien puestos desde abajo en la pila i) y visited (hashes de los layouts
    ya recorridos en esta construcción, o None si no se registran).

    Consultas: h(i) altura, e(i) huecos, g(i) grupo del tope (una pila vacía vale G),
    is_sorted_stack(i), is_sorted(), bad() (mal puestos: cota inferior de los movimientos
    que faltan), ub(i) (mal puestos desbloqueados), after(so, sd) (hash del layout que deja
    un movimiento, sin hacerlo)."""

    __slots__ = ("stacks", "H", "G", "N", "sorted_n", "moves", "visited")

    def __init__(self, stacks, H: int, G: int, track: bool = False):
        self.stacks = [list(s) for s in stacks]
        self.H, self.G = H, G
        self.N = sum(len(s) for s in self.stacks)
        self.sorted_n = [self._count_sorted(s) for s in self.stacks]
        self.moves: list[tuple[int, int]] = []
        self.visited: set[int] | None = {self.state_hash()} if track else None

    @classmethod
    def from_instance(cls, inst: CPMPInstance, track: bool = False) -> "Layout":
        return cls(inst.stacks, inst.H, inst.G, track=track)

    @staticmethod
    def _count_sorted(s) -> int:
        n = 1 if s else 0
        while n < len(s) and s[n] <= s[n - 1]:
            n += 1
        return n

    def copy(self, track: bool | None = None) -> "Layout":
        c = Layout.__new__(Layout)
        c.stacks = [list(s) for s in self.stacks]
        c.H, c.G, c.N = self.H, self.G, self.N
        c.sorted_n = list(self.sorted_n)
        c.moves = list(self.moves)
        keep = self.visited is not None if track is None else track
        c.visited = (set(self.visited) if self.visited is not None else {self.state_hash()}) if keep else None
        return c

    # --- consultas ---------------------------------------------------------------------
    @property
    def S(self) -> int:
        return len(self.stacks)

    def h(self, i: int) -> int:
        return len(self.stacks[i])

    def e(self, i: int) -> int:
        return self.H - len(self.stacks[i])

    def g(self, i: int) -> int:
        return self.stacks[i][-1] if self.stacks[i] else self.G

    def is_sorted_stack(self, i: int) -> bool:
        return self.sorted_n[i] == len(self.stacks[i])

    def is_sorted(self) -> bool:
        return all(self.sorted_n[i] == len(s) for i, s in enumerate(self.stacks))

    def bad(self) -> int:
        return sum(len(s) - n for s, n in zip(self.stacks, self.sorted_n))

    def ub(self, i: int) -> int:
        """Mal puestos desbloqueados de la pila i: el tramo del tope, por encima de la parte
        ordenada, con grupos no crecientes de abajo hacia arriba (se pueden bien poner con
        movimientos sucesivos sobre una pila ordenada con grupo suficiente)."""
        s, n = self.stacks[i], self.sorted_n[i]
        if n == len(s):
            return 0
        j, count = len(s) - 1, 1
        while j - 1 >= n and s[j - 1] >= s[j]:
            j, count = j - 1, count + 1
        return count

    def valid(self, so: int, sd: int) -> bool:
        return so != sd and bool(self.stacks[so]) and len(self.stacks[sd]) < self.H

    def state(self) -> tuple:
        return tuple(tuple(s) for s in self.stacks)

    def state_hash(self) -> int:
        return hash(self.state())

    def after(self, so: int, sd: int) -> int:
        stacks = [tuple(s) for s in self.stacks]
        c = stacks[so][-1]
        stacks[so] = stacks[so][:-1]
        stacks[sd] = stacks[sd] + (c,)
        return hash(tuple(stacks))

    # --- movimientos -------------------------------------------------------------------
    def move(self, so: int, sd: int) -> None:
        if not self.valid(so, sd):
            raise ValueError(f"movimiento inválido {(so, sd)}")
        c = self.stacks[so].pop()
        self.sorted_n[so] = min(self.sorted_n[so], len(self.stacks[so]))
        if self.sorted_n[sd] == len(self.stacks[sd]) and c <= self.g(sd):
            self.sorted_n[sd] += 1
        self.stacks[sd].append(c)
        self.moves.append((so, sd))
        if self.visited is not None:
            self.visited.add(self.state_hash())


__all__ = ["Layout"]
