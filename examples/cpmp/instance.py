"""Instancias del CPMP (Container Pre-Marshalling Problem).

Un layout tiene S pilas de altura máxima H; cada pila es una tupla de grupos de abajo hacia
arriba (grupo mayor = se retira después). Es factible cuando toda pila está ordenada:
grupos no crecientes de abajo hacia arriba. El objetivo es la cantidad de movimientos.

Generadores:
- `cvs_like`: al estilo Caserta et al. (2011): todas las pilas con H − 2 contenedores
  (N = S·(H − 2)) y grupos distintos 1..N;
- `bf_like`: al estilo Bortfeldt y Forster (2012): N = fill·S·H y G = group_ratio·N grupos,
  repartidos al azar entre pilas.
`parse` lee el formato de texto de los benchmarks CVS/BF ("Tiers: H", "Stacks: S",
"Stack i: g g g", de abajo hacia arriba).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class CPMPInstance:
    stacks: tuple[tuple[int, ...], ...]
    H: int
    name: str = ""

    @property
    def S(self) -> int:
        return len(self.stacks)

    @property
    def N(self) -> int:
        return sum(len(s) for s in self.stacks)

    @property
    def G(self) -> int:
        return max((g for s in self.stacks for g in s), default=1)

    def __post_init__(self):
        if any(len(s) > self.H for s in self.stacks):
            raise ValueError("una pila supera la altura máxima H")
        if self.N > (self.S - 1) * self.H:
            raise ValueError("N > (S − 1)·H: no siempre se puede vaciar una pila")

    @classmethod
    def cvs_like(cls, S: int, H: int, rng: Random, name: str = "") -> "CPMPInstance":
        N = S * (H - 2)
        groups = list(range(1, N + 1))
        rng.shuffle(groups)
        h = H - 2
        stacks = tuple(tuple(groups[i * h:(i + 1) * h]) for i in range(S))
        return cls(stacks, H, name or f"cvs_{S}x{H}")

    @classmethod
    def bf_like(cls, S: int, H: int, rng: Random, fill: float = 0.6, group_ratio: float = 0.2,
                name: str = "") -> "CPMPInstance":
        N = max(1, round(fill * S * H))
        G = max(1, round(group_ratio * N))
        stacks: list[list[int]] = [[] for _ in range(S)]
        for _ in range(N):
            free = [i for i in range(S) if len(stacks[i]) < H]
            stacks[rng.choice(free)].append(rng.randint(1, G))
        return cls(tuple(tuple(s) for s in stacks), H, name or f"bf_{S}x{H}")

    @classmethod
    def parse(cls, text: str, name: str = "") -> "CPMPInstance":
        H = int(re.search(r"Tiers\s*:\s*(\d+)", text).group(1))
        stacks = [tuple(int(v) for v in m.group(1).split())
                  for m in re.finditer(r"Stack\s+\d+\s*:([^\n]*)", text)]
        return cls(tuple(stacks), H, name)

    @classmethod
    def load(cls, path: str) -> "CPMPInstance":
        with open(path) as f:
            return cls.parse(f.read(), name=path)


def is_sorted_stack(stack) -> bool:
    return all(stack[i] >= stack[i + 1] for i in range(len(stack) - 1))


__all__ = ["CPMPInstance", "is_sorted_stack"]
