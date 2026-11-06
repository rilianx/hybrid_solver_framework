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
    rounded: bool = False  # distancias redondeadas al entero más cercano (EUC_2D de TSPLIB, las instancias X de Uchoa)

    @property
    def n_customers(self) -> int:
        return len(self.coords) - 1

    @property
    def customers(self) -> range:
        return range(1, len(self.coords))

    def dist(self, i: int, j: int) -> float:
        (xi, yi), (xj, yj) = self.coords[i], self.coords[j]
        d = math.hypot(xi - xj, yi - yj)
        return float(int(d + 0.5)) if self.rounded else d

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

    @staticmethod
    def unit_square(n_customers: int, rng: Random) -> "CVRPInstance":
        """Como las de ReEvo, MCTS-AHD y HSEvo (`problems/cvrp_aco/gen_inst.py`): depósito en (0.5, 0.5), clientes
        uniformes en el cuadrado unitario, demandas enteras 1–9, capacidad 50, distancias reales."""
        coords = [(0.5, 0.5)] + [(rng.random(), rng.random()) for _ in range(n_customers)]
        demand = [0.0] + [float(rng.randint(1, 9)) for _ in range(n_customers)]
        return CVRPInstance(tuple(coords), tuple(demand), 50.0)

    @staticmethod
    def uchoa_like(n_customers: int, rng: Random) -> "CVRPInstance":
        """Como las instancias X (Uchoa et al., 2017), para afinar sin usar las del benchmark: grilla [0, 1000]²
        entera y distancias redondeadas; depósito central, excéntrico o al azar; clientes al azar, agrupados o mitad
        y mitad; demandas de uno de los siete tipos del artículo; capacidad para rutas de 3 a 25 clientes en promedio."""
        depot = rng.choice([(500, 500), (0, 0), (rng.randint(0, 1000), rng.randint(0, 1000))])
        kind = rng.choice(["R", "C", "RC"])
        seeds = [(rng.randint(0, 1000), rng.randint(0, 1000)) for _ in range(rng.randint(3, 8))]
        coords = [depot]
        for k in range(n_customers):
            if kind == "R" or (kind == "RC" and k % 2 == 0):
                coords.append((rng.randint(0, 1000), rng.randint(0, 1000)))
            else:
                cx, cy = rng.choice(seeds)
                coords.append((min(1000, max(0, round(rng.gauss(cx, 60)))), min(1000, max(0, round(rng.gauss(cy, 60))))))
        dem = rng.choice(["unit", "1-10", "5-10", "1-100", "50-100", "quadrant", "many-small"])

        def demand(x, y):
            if dem == "unit":
                return 1
            if dem == "quadrant":
                return rng.randint(51, 100) if (x >= 500) == (y >= 500) else rng.randint(1, 50)
            if dem == "many-small":
                return rng.randint(1, 10) if rng.random() < rng.uniform(0.7, 0.95) else rng.randint(50, 100)
            lo, hi = map(int, dem.split("-"))
            return rng.randint(lo, hi)

        demands = [0.0] + [float(demand(x, y)) for x, y in coords[1:]]
        r = rng.triangular(3, 25, 6)
        capacity = float(max(max(demands), math.ceil(r * sum(demands) / n_customers)))
        return CVRPInstance(tuple((float(x), float(y)) for x, y in coords), tuple(demands), capacity, rounded=True)

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(self.to_text())

    def to_text(self) -> str:
        """Formato de entrada (como un problema de Codeforces): `n Q` (y `round` si las distancias se redondean),
        luego n+1 líneas `x y d` (la primera es el depósito, con d = 0)."""
        lines = [f"{self.n_customers} {_num(self.capacity)}" + (" round" if self.rounded else "")]
        lines += [f"{_num(x)} {_num(y)} {_num(d)}" for (x, y), d in zip(self.coords, self.demand)]
        return "\n".join(lines) + "\n"

    @staticmethod
    def parse(text: str) -> "CVRPInstance":
        lines = [ln for ln in text.splitlines() if ln.strip()]
        head = lines[0].split()
        n, cap = head[0], head[1]
        rows = [tuple(map(float, ln.split())) for ln in lines[1:]]
        assert len(rows) == int(n) + 1, "se esperaban n+1 filas (depósito + clientes)"
        return CVRPInstance(tuple((x, y) for x, y, _ in rows), tuple(d for _, _, d in rows), float(cap),
                            rounded=len(head) > 2 and head[2] == "round")

    @staticmethod
    def parse_vrplib(text: str, rounded: bool = True) -> "CVRPInstance":
        """El formato VRPLIB de CVRPLIB (EUC_2D, un depósito): las instancias X de Uchoa et al. (2017). `rounded`: la
        convención de CVRPLIB (distancias redondeadas); las Golden y las aleatorias de FrontierCO usan las reales. Se
        ignora DISTANCE (largo máximo de ruta), como en FrontierCO."""
        sec, coords, demand, cap, depot = None, {}, {}, None, 1
        for ln in text.splitlines():
            tok = ln.replace(":", " : ").split()
            if not tok:
                continue
            if tok[0] == "CAPACITY":
                cap = float(tok[-1])
            elif tok[0].endswith("_SECTION"):
                sec = tok[0]
            elif tok[0] in ("EOF", "-1"):
                sec = None if tok[0] == "EOF" else sec
            elif sec == "NODE_COORD_SECTION":
                coords[int(tok[0])] = (float(tok[1]), float(tok[2]))
            elif sec == "DEMAND_SECTION":
                demand[int(tok[0])] = float(tok[1])
            elif sec == "DEPOT_SECTION" and int(tok[0]) > 0:
                depot = int(tok[0])
        order = [depot] + [k for k in sorted(coords) if k != depot]
        return CVRPInstance(tuple(coords[k] for k in order), tuple(0.0 if k == depot else demand[k] for k in order),
                            cap, rounded=rounded)

    @staticmethod
    def load(path: str) -> "CVRPInstance":
        with open(path) as f:
            text = f.read()
        return CVRPInstance.parse_vrplib(text) if "NODE_COORD_SECTION" in text else CVRPInstance.parse(text)


def _num(v: float) -> str:
    """Sin pérdida: entero si lo es, si no la representación exacta del float."""
    return str(int(v)) if float(v).is_integer() else repr(float(v))
