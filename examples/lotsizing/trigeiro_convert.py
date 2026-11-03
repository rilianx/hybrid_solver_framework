"""Las instancias de Trigeiro, Thomas y McClain (1989) de strIPlib (`lotsizing/single-level/trigeiro/textbook`, en
formato LP de Zimpl) al formato de `CLSPInstance`: el modelo es el mismo (costos y tiempos de setup, inventario, una
capacidad por período, sin backlog ni inventario inicial). Las G tienen un tiempo por unidad alpha_i ≠ 1: se mide cada
ítem en unidades de tiempo (x' = alpha·x, d' = alpha·d, h' = h/alpha), el mismo problema con alpha = 1 y el mismo costo.

    python -m examples.lotsizing.trigeiro_convert <directorio con *.lp.gz> examples/lotsizing/trigeiro
"""

from __future__ import annotations

import gzip
import re
import sys
from pathlib import Path

from .instance import CLSPInstance

TERM = re.compile(r"([+-])\s*(\d+(?:\.\d+)?(?:e[+-]?\d+)?)?\s*([xys])#(\d+)#(\d+)")


def _terms(text: str):
    for sign, coef, var, t, i in TERM.findall(text):
        c = float(coef) if coef else 1.0
        yield (-c if sign == "-" else c), var, int(t) - 1, int(i) - 1


def parse_lp(text: str) -> CLSPInstance:
    body = text.split("\nMinimize", 1)[1]
    obj, rest = body.split("Subject to", 1)
    cons = rest.split("\nBounds", 1)[0]
    h, q = {}, {}
    for c, var, _t, i in _terms(obj.split(":", 1)[1]):
        (h if var == "s" else q)[i] = c
    demand, cap, beta, alpha = {}, {}, {}, {}
    for name, expr in re.findall(r"\n\s*(\w+):\s*(.*?)(?=\n\s*\w+:|\Z)", cons, re.S):
        lhs, op, rhs = re.split(r"\s*(<=|>=|=)\s*", expr.strip(), maxsplit=1)
        rhs = float(rhs.split()[0])
        if name.startswith("balance"):
            ts = [(t, i) for c, v, t, i in _terms(lhs) if v == "x"]
            assert len(ts) == 1
            demand[ts[0]] = rhs
        elif name.startswith("capacity"):
            for c, v, t, i in _terms(lhs):
                (beta if v == "y" else alpha)[i] = c
                cap[t] = rhs
    n_items, n_periods = len(q), len(cap)
    assert len(h) == n_items and len(demand) == n_items * n_periods and len(alpha) == n_items
    a = [alpha[i] for i in range(n_items)]
    return CLSPInstance(
        demand=tuple(tuple(demand[t, i] * a[i] for t in range(n_periods)) for i in range(n_items)),
        setup_cost=tuple(q[i] for i in range(n_items)), holding_cost=tuple(h[i] / a[i] for i in range(n_items)),
        setup_time=tuple(beta[i] for i in range(n_items)), capacity=tuple(cap[t] for t in range(n_periods)))


def main() -> None:
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    dst.mkdir(parents=True, exist_ok=True)
    for p in sorted(src.glob("*.lp.gz")):
        try:
            inst = parse_lp(gzip.open(p, "rt").read())
        except (OSError, EOFError) as exc:  # F19N viene dañado en la descarga de strIPlib
            print(f"{p.name}: no se pudo leer ({exc})", file=sys.stderr)
            continue
        inst.save(str(dst / (p.name.removesuffix(".lp.gz") + ".txt")))
        print(p.name, inst.n_items, inst.n_periods)


if __name__ == "__main__":
    main()
