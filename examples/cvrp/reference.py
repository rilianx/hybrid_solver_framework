"""Referencias para los conjuntos sin valor publicado (los test de ReEvo): la mejor solución de HGS (PyVRP, Wouda et al.
2024), la mejor de varias semillas en un tiempo fijo, evaluada con el oráculo en distancias reales.

    pip install pyvrp
    python -m examples.cvrp.reference reevo --seconds 10 --seeds 3 --workers 4

PyVRP trabaja con distancias enteras: se escalan para que la mayor sea del orden de 10^5 y se redondean para la búsqueda
(una escala mayor desbalancea las penalizaciones de PyVRP); el costo que se guarda es el
de las rutas encontradas con las distancias reales. HGS no prueba optimalidad: es una mejor conocida (`ub`), no un
óptimo. Guarda `<conjunto>/best_known.json` con {instancia: {"ub", "routes", "source"}}.
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from . import model_parts as ref
from .instance import CVRPInstance

HERE = Path(__file__).parent
TARGET = 10**5


def hgs(inst: CVRPInstance, seconds: float, seed: int = 0) -> list[list[int]]:
    from pyvrp import Model
    from pyvrp.stop import MaxRuntime

    span = max(max(x for x, _ in inst.coords) - min(x for x, _ in inst.coords),
               max(y for _, y in inst.coords) - min(y for _, y in inst.coords), 1e-9)
    scale = 1 if inst.rounded else TARGET / span
    m = Model()
    m.add_vehicle_type(num_available=inst.n_customers, capacity=[int(round(inst.capacity))])
    locs = [m.add_location(x=int(round(x * scale)), y=int(round(y * scale))) for x, y in inst.coords]
    m.add_depot(locs[0])
    for c in inst.customers:
        m.add_client(locs[c], delivery=[int(round(inst.demand[c]))])
    for a in range(len(locs)):
        for b in range(len(locs)):
            if a != b:
                m.add_edge(locs[a], locs[b], distance=int(round(inst.dist(a, b) * scale)))
    res = m.solve(stop=MaxRuntime(seconds), seed=seed, display=False)
    # las actividades de cliente traen el índice del cliente (0..n-1, en el orden agregado); el nodo es idx + 1
    return [[a.idx + 1 for a in r if a.is_client()] for r in res.best.routes()]


def _job(args):
    """La mejor de `seeds` corridas de HGS (con una sola, a veces se queda en un óptimo local: en instance_100_1 de
    FrontierCO la semilla 0 da 1331.67 y las 2 y 3, la referencia publicada, 1322.22)."""
    path, seconds, seeds = args
    inst = CVRPInstance.load(str(path))
    best = None
    for seed in range(seeds):
        routes = hgs(inst, seconds, seed)
        sol = ref.from_answer(inst, routes)
        assert not any(ref.violations(inst, sol).values()), path
        cost = ref.cost_terms(inst, sol)["distancia"]
        if best is None or cost < best[0]:
            best = (cost, routes)
    return path.stem, {"ub": round(best[0], 6), "routes": best[1],
                       "source": f"HGS (PyVRP), mejor de {seeds} semillas × {seconds:g} s"}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("set", help="directorio de examples/cvrp (p.ej. reevo)")
    ap.add_argument("--seconds", type=float, default=20)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args(argv)
    d = HERE / args.set
    out_path = d / "best_known.json"
    out = json.loads(out_path.read_text()) if out_path.exists() else {}
    todo = [p for p in sorted(d.glob("*.txt")) if p.stem not in out]
    with ProcessPoolExecutor(args.workers) as ex:
        for name, res in ex.map(_job, [(p, args.seconds, args.seeds) for p in todo]):
            out[name] = res
            out_path.write_text(json.dumps(dict(sorted(out.items())), indent=1) + "\n")
            print(name, res["ub"], flush=True)


if __name__ == "__main__":
    main()
