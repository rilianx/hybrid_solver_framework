"""Los benchmarks del CVRP: los de la literatura de OR y los de los trabajos de diseño de heurísticas con LLM.

    python -m examples.cvrp.fetch            # X completo, FrontierCO y ReEvo

| directorio | conjunto | instancias | distancias | referencia |
|---|---|---|---|---|
| `uchoa/` | X de Uchoa et al. (2017) | 100 (101–1001 clientes) | redondeadas | mejor conocida de CVRPLIB |
| `frontierco/` | CVRP de FrontierCO (ICLR 2026): Golden et al. (1998) "easy", aleatorias "valid" | 20 + 15 | reales | la de FrontierCO |
| `frontierco/` | FrontierCO "hard": Arnold, Gendreau y Sörensen (2019), Bélgica | 10 | redondeadas | mejor conocida de CVRPLIB |
| `reevo/` | test20/50/100 de ReEvo (NeurIPS 2024; los usan también MCTS-AHD y HSEvo) | 3 × 64 | reales | sin referencia publicada |

FrontierCO ignora el largo máximo de ruta (DISTANCE) de las Golden 1–8; aquí también. Las de ReEvo se reproducen con
su generador (`problems/cvrp_aco/gen_inst.py`: numpy, semilla 1234; depósito en (0.5, 0.5), clientes uniformes en el
cuadrado unitario, demandas 1–9, capacidad 50), en el mismo orden de llamadas, así que son las mismas instancias.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from .instance import CVRPInstance

HERE = Path(__file__).parent
PYVRP = "https://github.com/PyVRP/Instances.git"
HF = "https://huggingface.co/datasets/CO-Bench/FrontierCO/resolve/main/CVRP"
GOLDEN = [f"easy_test_instances/Golden_{k}.vrp" for k in range(1, 21)]
VALID = [f"valid_instances/instance_{n}_{k}.vrp" for n in (20, 50, 100) for k in range(1, 6)]
ARNOLD = [f"hard_test_instances/{c}{k}.vrp" for c in ("Antwerp", "Brussels", "Flanders", "Ghent", "Leuven") for k in (1, 2)]


def _get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=600) as r:
        return r.read()


def _save_refs(d: Path, refs: dict[str, float], source: str) -> None:
    data = {"_fuente": source}
    data.update(dict(sorted(refs.items())))
    (d / "best_known.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


def fetch_x() -> None:
    d = HERE / "uchoa"
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "pyvrp"
        subprocess.run(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--no-checkout", PYVRP, str(repo)],
                       check=True)
        subprocess.run(["git", "-C", str(repo), "checkout", "-q", "HEAD", "--", "CVRP"], check=True)
        refs = {}
        for f in sorted((repo / "CVRP").glob("X-*.vrp")):
            (d / f.name).write_bytes(f.read_bytes())
            cost = re.search(r"Cost\s+([\d.]+)", f.with_suffix(".sol").read_text()).group(1)
            refs[f.stem] = float(cost)
    _save_refs(d, refs, "CVRPLIB, conjunto X (Uchoa et al., 2017), vía github.com/PyVRP/Instances: mejores soluciones "
                        "conocidas (distancias redondeadas)")


def fetch_frontierco() -> None:
    d = HERE / "frontierco"
    d.mkdir(exist_ok=True)
    config = _get(f"{HF}/config.py").decode()
    published = {k: float(v) for k, v in re.findall(r"'([a-z_]+/[A-Za-z0-9_]+\.vrp)': \[([0-9.]+)\]", config)}
    refs = {}
    for path in GOLDEN + VALID + ARNOLD:
        rounded = path in ARNOLD  # las de Arnold siguen la convención de CVRPLIB (su referencia es entera)
        inst = CVRPInstance.parse_vrplib(_get(f"{HF}/{path}").decode(), rounded=rounded)
        name = Path(path).stem
        inst.save(str(d / f"{name}.txt"))
        refs[name] = published[path]
    _save_refs(d, refs, "FrontierCO (huggingface.co/datasets/CO-Bench/FrontierCO, CVRP/config.py): las referencias con "
                        "las que normaliza. Golden y valid con distancias reales (sin el largo máximo de ruta de las "
                        "Golden 1–8); las de Arnold (Antwerp…Leuven), redondeadas como en CVRPLIB.")


def reevo_instances() -> dict[str, list[CVRPInstance]]:
    """Los conjuntos test20/50/100 de ReEvo, reproducidos con su generador y su semilla."""
    import numpy as np

    def gen(n):
        loc = np.random.rand(n, 2)
        dem = np.random.randint(low=1, high=10, size=n)
        coords = ((0.5, 0.5),) + tuple((float(x), float(y)) for x, y in loc)
        return CVRPInstance(coords, (0.0,) + tuple(float(q) for q in dem), 50.0)

    np.random.seed(1234)
    for _ in range(10):  # train50
        gen(50)
    for n in (20, 50, 100):  # val
        for _ in range(64):
            gen(n)
    return {f"test{n}": [gen(n) for _ in range(64)] for n in (20, 50, 100)}


def fetch_reevo() -> None:
    d = HERE / "reevo"
    d.mkdir(exist_ok=True)
    for group, insts in reevo_instances().items():
        for k, inst in enumerate(insts):
            inst.save(str(d / f"{group}_{k:02d}.txt"))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--only", nargs="*", default=None, help="x frontierco reevo")
    args = ap.parse_args(argv)
    only = set(args.only or ["x", "frontierco", "reevo"])
    if "x" in only:
        fetch_x()
    if "frontierco" in only:
        fetch_frontierco()
    if "reevo" in only:
        fetch_reevo()


if __name__ == "__main__":
    main()
