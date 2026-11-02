"""Instancia del flow shop de permutación (datos solamente), en el formato de Taillard (1993)."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class PFSPInstance:
    p: tuple[tuple[int, ...], ...]  # p[i][j] = tiempo de proceso del trabajo j en la máquina i

    @property
    def n_jobs(self) -> int:
        return len(self.p[0])

    @property
    def n_machines(self) -> int:
        return len(self.p)

    @staticmethod
    def random(n_jobs: int, n_machines: int, rng: Random) -> "PFSPInstance":
        """Tiempos enteros uniformes en [1, 99], como en Taillard (1993)."""
        return PFSPInstance(tuple(tuple(rng.randint(1, 99) for _ in range(n_jobs)) for _ in range(n_machines)))

    def to_text(self) -> str:
        """Formato de entrada: `n m` (trabajos, máquinas) y luego m líneas, una por máquina, con los n tiempos de proceso."""
        return "\n".join([f"{self.n_jobs} {self.n_machines}"] + [" ".join(str(v) for v in row) for row in self.p]) + "\n"

    @staticmethod
    def parse(text: str) -> "PFSPInstance":
        nums = [int(float(x)) for x in text.split()]
        n, m = nums[0], nums[1]
        vals = nums[2:2 + n * m]
        assert len(vals) == n * m, "faltan tiempos de proceso"
        return PFSPInstance(tuple(tuple(vals[i * n:(i + 1) * n]) for i in range(m)))

    @staticmethod
    def load(path: str) -> "PFSPInstance":
        with open(path) as f:
            return PFSPInstance.parse(f.read())
