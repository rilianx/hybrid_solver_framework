"""Los benchmarks de la mochila multidimensional: la OR-Library y los test de ReEvo.

    python -m examples.mkp.fetch             # OR-Library (en el repositorio)
    python -m examples.mkp.fetch --reevo     # además los test de ReEvo (unos 16 MB; fuera de git)

| directorio | conjunto | instancias | ítems×recursos | referencia |
|---|---|---|---|---|
| `orlib/` | mknapcb1–9, Chu y Beasley (1998) | 270 | 100–500 × 5–30 | mejor conocida (CO-Bench) |
| `orlib/` | mknap1, Petersen (1967) | 7 | 6–50 × 5–10 | óptimo |
| `orlib/` | mknap2, 48 de la literatura (consumos leídos por recurso; ver `parse_mknap2`) (Senyu y Toyada, Weingartner y Ness, Shi, Fréville y Plateau…) | 48 | 10–105 × 2–30 | óptimo |
| `reevo/` (`--reevo`) | test100/200/300/500/1000 de ReEvo (NeurIPS 2024; también MCTS-AHD) | 5 × 64 | 100–1000 × 5 | óptimo (CBC, `reference.py`; `reevo_best_known.json`) |

La OR-Library viene del MKP de CO-Bench (huggingface.co/datasets/CO-Bench/CO-Bench), con las referencias con las que
normaliza (`config.py`). En mknap2 CO-Bench transpone la matriz de consumos; aquí no (`parse_mknap2`). Los de ReEvo se reproducen con su generador (`problems/mkp_aco/gen_inst.py`: numpy,
semilla 4567; beneficios U(0,1), consumos U(0,1) normalizados para que todas las capacidades sean 1).
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from pathlib import Path

from .instance import MKPInstance

HERE = Path(__file__).parent
HF = "https://huggingface.co/datasets/CO-Bench/CO-Bench/resolve/main/Multidimensional%20knapsack%20problem"
FILES = ["mknap1"] + [f"mknapcb{k}" for k in range(1, 10)]


def _get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=600) as r:
        return r.read().decode()


def parse_orlib(text: str) -> list[MKPInstance]:
    """mknap1 y mknapcb*: K casos; cada uno `n m opt`, los n beneficios, m filas de n consumos y las m capacidades."""
    tok = text.split()
    k, p, out = int(tok[0]), 1, []
    for _ in range(k):
        n, m = int(tok[p]), int(tok[p + 1])
        p += 3
        vals = [float(t) for t in tok[p:p + n + m * n + m]]
        p += n + m * n + m
        out.append(MKPInstance(tuple(vals[:n]), tuple(tuple(vals[n + i * n:n + (i + 1) * n]) for i in range(m)),
                               tuple(vals[n + m * n:])))
    return out


def parse_mknap2(text: str) -> list[tuple[MKPInstance, float | None]]:
    """mknap2: sin comentarios (`//`), se buscan cabeceras `m n` (como `load_data2` de CO-Bench) y se leen los n
    beneficios, las m capacidades, la matriz de consumos POR RECURSO (m filas de n) y el óptimo si viene. CO-Bench la
    lee por ítem (n filas de m), lo que da otras instancias: en 23 de las 48 la greedy supera el óptimo publicado; leída
    por recurso, CBC reproduce los óptimos."""
    tokens = " ".join(line.split("//")[0].strip() for line in text.splitlines()).split()
    out, i, N = [], 0, len(tokens)
    while i < N - 1:
        try:
            m, n = int(float(tokens[i])), int(float(tokens[i + 1]))
        except ValueError:
            i += 1
            continue
        if m <= 0 or n <= 0:
            i += 1
            continue
        if i + 2 + n + m + n * m > N:
            break
        i += 2
        profit = [float(t) for t in tokens[i:i + n]]
        i += n
        cap = [float(t) for t in tokens[i:i + m]]
        i += m
        weight = tuple(tuple(float(t) for t in tokens[i + r * n:i + (r + 1) * n]) for r in range(m))
        i += n * m
        opt = None
        if i < N:
            try:
                opt = float(tokens[i])
                i += 1
            except ValueError:
                pass
        out.append((MKPInstance(tuple(profit), weight, tuple(cap)), opt))
    return out


def fetch_orlib() -> None:
    d = HERE / "orlib"
    d.mkdir(exist_ok=True)
    config = _get(f"{HF}/config.py")
    refs = {}
    for f in FILES + ["mknap2"]:
        values = [float(v) for v in re.search(rf"""["']{f}\.txt["']: \[([^\]]*)\]""", config).group(1).split(",")]
        text = _get(f"{HF}/{f}.txt")
        insts = [x for x, _ in parse_mknap2(text)] if f == "mknap2" else parse_orlib(text)
        assert len(insts) == len(values), (f, len(insts), len(values))
        for k, (inst, best) in enumerate(zip(insts, values)):
            name = f"{f}_{k + 1:02d}"
            inst.save(str(d / f"{name}.txt"))
            refs[name] = -best  # el costo es el beneficio con signo menos
    data = {"_fuente": "CO-Bench (huggingface.co/datasets/CO-Bench/CO-Bench, Multidimensional knapsack problem, "
                       "config.py): la mejor conocida (mknapcb) u óptimo (mknap1, mknap2), como costo = -beneficio."}
    data.update(refs)
    (d / "best_known.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


def reevo_instances() -> dict[str, list[MKPInstance]]:
    """Los test de ReEvo, reproducidos con su generador y su semilla (m = 5 recursos; 64 instancias por tamaño)."""
    import numpy as np

    np.random.seed(4567)
    out = {}
    for n in (100, 200, 300, 500, 1000):
        insts = []
        for _ in range(64):
            prize = np.random.rand(n)
            weight = np.random.rand(n, 5)
            cons = np.random.uniform(low=weight.max(0), high=weight.sum(0))
            weight = weight / cons.reshape(1, 5)
            insts.append(MKPInstance(tuple(float(p) for p in prize),
                                     tuple(tuple(float(weight[j, i]) for j in range(n)) for i in range(5)),
                                     (1.0,) * 5))
        out[f"test{n}"] = insts
    return out


def fetch_reevo() -> None:
    d = HERE / "reevo"
    d.mkdir(exist_ok=True)
    for group, insts in reevo_instances().items():
        for k, inst in enumerate(insts):
            inst.save(str(d / f"{group}_{k:02d}.txt"))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--reevo", action="store_true", help="también los test de ReEvo (fuera de git)")
    args = ap.parse_args(argv)
    fetch_orlib()
    if args.reevo:
        fetch_reevo()


if __name__ == "__main__":
    main()
