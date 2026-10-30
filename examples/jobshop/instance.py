"""Instancia del job shop (datos solamente). Separada del modelo para que la generación del modelo
con LLM pueda ver la instancia sin ver las piezas de referencia."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class JSSPInstance:
    # routes[j] = ruta del trabajo j: tupla de operaciones (máquina, tiempo de proceso) en el orden obligatorio
    routes: tuple[tuple[tuple[int, int], ...], ...]
    n_machines: int

    @property
    def n_jobs(self) -> int:
        return len(self.routes)

    @property
    def jobs(self) -> range:
        return range(len(self.routes))

    @property
    def machines(self) -> range:
        return range(self.n_machines)

    def machine(self, j: int, k: int) -> int:
        return self.routes[j][k][0]

    def proc(self, j: int, k: int) -> int:
        return self.routes[j][k][1]

    def op_index(self, j: int, m: int) -> int | None:
        """Posición en la ruta del trabajo j de su operación en la máquina m (None si no pasa por m)."""
        for k, (mm, _) in enumerate(self.routes[j]):
            if mm == m:
                return k
        return None

    def horizon(self) -> int:
        """Suma de todos los tiempos de proceso: cota superior de cualquier inicio de un plan semiactivo."""
        return sum(p for r in self.routes for _, p in r)

    @staticmethod
    def random(n_jobs: int, n_machines: int, rng: Random) -> "JSSPInstance":
        """Como las de Taillard (1993): cada trabajo pasa una vez por cada máquina, en un orden al azar,
        con tiempos de proceso enteros uniformes en 1..99."""
        routes = []
        for _ in range(n_jobs):
            order = list(range(n_machines))
            rng.shuffle(order)
            routes.append(tuple((m, rng.randint(1, 99)) for m in order))
        return JSSPInstance(tuple(routes), n_machines)

    def to_text(self) -> str:
        """Formato de entrada (el de la OR-Library): `n m`, luego una línea por trabajo con los pares
        `máquina tiempo` de sus operaciones en orden (máquinas numeradas desde 0)."""
        lines = [f"{self.n_jobs} {self.n_machines}"]
        lines += [" ".join(f"{m} {p}" for m, p in r) for r in self.routes]
        return "\n".join(lines) + "\n"

    @staticmethod
    def parse(text: str) -> "JSSPInstance":
        lines = [ln for ln in text.splitlines() if ln.strip()]
        n, m = map(int, lines[0].split())
        routes = []
        for ln in lines[1:n + 1]:
            vals = list(map(int, ln.split()))
            routes.append(tuple((vals[i], vals[i + 1]) for i in range(0, len(vals), 2)))
        assert len(routes) == n, "se esperaban n líneas de trabajos"
        return JSSPInstance(tuple(routes), m)

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(self.to_text())

    @staticmethod
    def load(path: str) -> "JSSPInstance":
        with open(path) as f:
            return JSSPInstance.parse(f.read())
