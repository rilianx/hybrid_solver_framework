"""Instancia del CVRP (datos solamente). Separada del modelo para que la generación del
`ProblemModel` con LLM (`llm.model_generator`) pueda ver la instancia sin ver el modelo de referencia."""

from __future__ import annotations

import math
from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class CVRPInstance:
    coords: tuple[tuple[float, float], ...]  # coords[0] = depósito
    demand: tuple[float, ...]  # demand[0] = 0
    capacity: float

    @property
    def n_customers(self) -> int:
        return len(self.coords) - 1

    @property
    def customers(self) -> range:
        return range(1, len(self.coords))

    def dist(self, i: int, j: int) -> float:
        (xi, yi), (xj, yj) = self.coords[i], self.coords[j]
        return math.hypot(xi - xj, yi - yj)

    @staticmethod
    def random(n_customers: int, rng: Random, route_size: float = 5.0, clustered: bool = False) -> "CVRPInstance":
        """Clientes en [0, 100]², depósito en el centro, demandas 1–10. La capacidad se fija
        para que una ruta atienda en promedio `route_size` clientes. `clustered=True` agrupa
        a los clientes en 3–5 centros (como las instancias C de Solomon / X de Uchoa)."""
        coords = [(50.0, 50.0)]
        if clustered:
            centers = [(rng.uniform(10, 90), rng.uniform(10, 90)) for _ in range(rng.randint(3, 5))]
            for _ in range(n_customers):
                cx, cy = rng.choice(centers)
                coords.append((min(100.0, max(0.0, rng.gauss(cx, 8))), min(100.0, max(0.0, rng.gauss(cy, 8)))))
        else:
            coords += [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(n_customers)]
        coords = [(round(x, 1), round(y, 1)) for x, y in coords]
        demand = [0.0] + [float(rng.randint(1, 10)) for _ in range(n_customers)]
        capacity = float(max(max(demand), round(route_size * sum(demand) / n_customers)))
        return CVRPInstance(tuple(coords), tuple(demand), capacity)

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(f"{self.n_customers} {self.capacity}\n")
            for (x, y), d in zip(self.coords, self.demand):
                f.write(f"{x} {y} {d}\n")

    @staticmethod
    def load(path: str) -> "CVRPInstance":
        with open(path) as f:
            n, cap = f.readline().split()
            rows = [tuple(map(float, line.split())) for line in f if line.strip()]
        assert len(rows) == int(n) + 1
        return CVRPInstance(tuple((x, y) for x, y, _ in rows), tuple(d for _, _, d in rows), float(cap))
