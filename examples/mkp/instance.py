"""Instancia de la mochila multidimensional (MKP; datos solamente). Separada del modelo para que la generación del modelo
con LLM pueda ver la instancia sin ver las piezas de referencia."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class MKPInstance:
    profit: tuple[float, ...]  # profit[j]: beneficio del ítem j
    weight: tuple[tuple[float, ...], ...]  # weight[i][j]: consumo del recurso i por el ítem j
    capacity: tuple[float, ...]  # capacity[i]: disponibilidad del recurso i

    @property
    def n_items(self) -> int:
        return len(self.profit)

    @property
    def n_resources(self) -> int:
        return len(self.capacity)

    @property
    def items(self) -> range:
        return range(len(self.profit))

    @property
    def resources(self) -> range:
        return range(len(self.capacity))

    @staticmethod
    def random(n_items: int, n_resources: int, rng: Random, tightness: float | None = None) -> "MKPInstance":
        """Como las de Chu y Beasley (1998, OR-Library mknapcb): consumos enteros uniformes en 0..1000, capacidad =
        `tightness` × consumo total del recurso (0.25, 0.5 o 0.75 al azar si no se da) y beneficios correlacionados con
        los consumos: Σ_i consumo / m + 500 · U(0, 1), redondeado."""
        t = tightness if tightness is not None else rng.choice([0.25, 0.5, 0.75])
        weight = [[float(rng.randint(0, 1000)) for _ in range(n_items)] for _ in range(n_resources)]
        capacity = [float(round(t * sum(row))) for row in weight]
        profit = [float(round(sum(weight[i][j] for i in range(n_resources)) / n_resources + 500 * rng.random()))
                  for j in range(n_items)]
        return MKPInstance(tuple(profit), tuple(tuple(r) for r in weight), tuple(capacity))

    def to_text(self) -> str:
        """Formato de entrada (el de la OR-Library sin la cabecera de cantidad de casos): `n m`; una línea con los n
        beneficios; m líneas, una por recurso, con los n consumos; una línea con las m capacidades."""
        lines = [f"{self.n_items} {self.n_resources}", " ".join(map(_num, self.profit))]
        lines += [" ".join(map(_num, row)) for row in self.weight]
        lines.append(" ".join(map(_num, self.capacity)))
        return "\n".join(lines) + "\n"

    @staticmethod
    def parse(text: str) -> "MKPInstance":
        tok = text.split()
        n, m = int(tok[0]), int(tok[1])
        vals = [float(t) for t in tok[2:2 + n + m * n + m]]
        assert len(vals) == n + m * n + m, "archivo incompleto"
        profit = tuple(vals[:n])
        weight = tuple(tuple(vals[n + i * n:n + (i + 1) * n]) for i in range(m))
        capacity = tuple(vals[n + m * n:])
        return MKPInstance(profit, weight, capacity)

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(self.to_text())

    @staticmethod
    def load(path: str) -> "MKPInstance":
        with open(path) as f:
            return MKPInstance.parse(f.read())


def _num(v: float) -> str:
    """Sin pérdida: entero si lo es, si no la representación exacta del float."""
    return str(int(v)) if float(v).is_integer() else repr(float(v))
