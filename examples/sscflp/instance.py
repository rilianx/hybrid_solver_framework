"""Instancia del SSCFLP (datos solamente). Separada del modelo para que la generación del modelo con LLM pueda ver la
instancia sin ver las piezas de referencia."""

from __future__ import annotations

import math
from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class SSCFLPInstance:
    capacity: tuple[float, ...]  # capacity[i]: capacidad del centro i
    fixed: tuple[float, ...]  # fixed[i]: costo fijo de abrir el centro i
    demand: tuple[float, ...]  # demand[j]: demanda del cliente j
    cost: tuple[tuple[float, ...], ...]  # cost[i][j]: costo de atender TODA la demanda del cliente j desde el centro i

    @property
    def n_facilities(self) -> int:
        return len(self.capacity)

    @property
    def n_customers(self) -> int:
        return len(self.demand)

    @property
    def facilities(self) -> range:
        return range(len(self.capacity))

    @property
    def customers(self) -> range:
        return range(len(self.demand))

    @staticmethod
    def random(n_facilities: int, n_customers: int, rng: Random, ratio: float | None = None) -> "SSCFLPInstance":
        """Como las de Holmberg et al. (1999): centros y clientes en [10, 200]², demandas enteras 10–50, costo de
        asignación = distancia euclidiana × demanda / 10 (redondeado), capacidades 100–500 escaladas para que la
        capacidad total sea `ratio` veces la demanda total (al azar entre 1.5 y 4 si no se da) y costos fijos que
        crecen con la capacidad (con ruido)."""
        fac = [(rng.uniform(10, 200), rng.uniform(10, 200)) for _ in range(n_facilities)]
        cus = [(rng.uniform(10, 200), rng.uniform(10, 200)) for _ in range(n_customers)]
        demand = [float(rng.randint(10, 50)) for _ in range(n_customers)]
        raw = [rng.uniform(100, 500) for _ in range(n_facilities)]
        r = ratio if ratio is not None else rng.uniform(1.5, 4.0)
        scale = r * sum(demand) / sum(raw)
        capacity = [float(max(max(demand), round(c * scale))) for c in raw]
        fixed = [float(round(rng.uniform(300, 700) + 4 * math.sqrt(c) * rng.uniform(5, 10))) for c in capacity]
        cost = [[float(round(math.dist(f, c) * d / 10)) for c, d in zip(cus, demand)] for f in fac]
        return SSCFLPInstance(tuple(capacity), tuple(fixed), tuple(demand), tuple(tuple(r) for r in cost))

    def to_text(self) -> str:
        """Formato de entrada (el de Holmberg et al., 1999): `n m`; n líneas `capacidad costo_fijo`; una línea con las m
        demandas; n líneas, una por centro, con los m costos de asignación `cost[i][0..m-1]`."""
        lines = [f"{self.n_facilities} {self.n_customers}"]
        lines += [f"{_num(s)} {_num(f)}" for s, f in zip(self.capacity, self.fixed)]
        lines.append(" ".join(map(_num, self.demand)))
        lines += [" ".join(map(_num, row)) for row in self.cost]
        return "\n".join(lines) + "\n"

    @staticmethod
    def parse(text: str) -> "SSCFLPInstance":
        """El formato de `to_text`; también los archivos de Holmberg, Yang, TB4 (Gadegaard) y Díaz-Fernández y los de
        MOrepo, que tienen el mismo orden (se ignora lo que venga después de la matriz de costos)."""
        tok = text.split()
        n, m = int(tok[0]), int(tok[1])
        vals = [float(t) for t in tok[2:2 + 2 * n + m + n * m]]
        assert len(vals) == 2 * n + m + n * m, "archivo incompleto"
        cap, fixed = tuple(vals[0:2 * n:2]), tuple(vals[1:2 * n:2])
        demand = tuple(vals[2 * n:2 * n + m])
        base = 2 * n + m
        cost = tuple(tuple(vals[base + i * m:base + (i + 1) * m]) for i in range(n))
        return SSCFLPInstance(cap, fixed, demand, cost)

    @staticmethod
    def parse_orlib(text: str) -> "SSCFLPInstance":
        """El formato de la OR-Library (capinfo, Beasley 1988: cap41–cap134, capa–capc): `n m`; n líneas `capacidad
        costo_fijo`; por cada cliente, su demanda y los n costos de asignarle toda su demanda a cada centro."""
        tok = text.split()
        n, m = int(tok[0]), int(tok[1])
        vals = [float(t) for t in tok[2:]]
        cap, fixed = tuple(vals[0:2 * n:2]), tuple(vals[1:2 * n:2])
        pos, demand, by_customer = 2 * n, [], []
        for _ in range(m):
            demand.append(vals[pos])
            by_customer.append(vals[pos + 1:pos + 1 + n])
            pos += 1 + n
        assert len(by_customer[-1]) == n, "archivo incompleto"
        cost = tuple(tuple(by_customer[j][i] for j in range(m)) for i in range(n))
        return SSCFLPInstance(cap, fixed, tuple(demand), cost)

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(self.to_text())

    @staticmethod
    def load(path: str) -> "SSCFLPInstance":
        """El formato de `to_text` (todos los archivos de `examples/sscflp/bench/` están convertidos a él; los dos
        formatos tienen la misma cantidad de números, así que no se distinguen solos)."""
        with open(path) as f:
            return SSCFLPInstance.parse(f.read())


def _num(v: float) -> str:
    """Sin pérdida: entero si lo es, si no la representación exacta del float."""
    return str(int(v)) if float(v).is_integer() else repr(float(v))
