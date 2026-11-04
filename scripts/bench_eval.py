"""Las configuraciones elegidas por corridas de tuning, en el benchmark de la literatura de cada problema, con el gap
contra la mejor solución conocida (un gap negativo es una mejor solución nueva).

    python -m scripts.bench_eval flowshop results/tune_run75 --t 60 --seeds 3 --out results/pfsp_run75.json
    python -m scripts.bench_eval jobshop results/tune_run83 --budget 30 --seeds 3
    python -m scripts.bench_eval cvrp results/tune_run81 --budget 30 --instances X-n101 X-n1
    python -m scripts.bench_eval clsp results/tune_run79 --budget 60 --instances G --extra base='{"skeleton": "ILS", ...}'

| problema | instancias | referencia | grupos |
|---|---|---|---|
| `flowshop`, `flowshop_cmax` | Taillard (`examples/flowshop/taillard/`) | mejores conocidas de flowtime / makespan | clase n_m |
| `jobshop` | Taillard ta01–ta20 (`examples/jobshop/taillard/`) | óptimo o mejor cota superior (JSPLIB) | 15×15, 20×15 |
| `cvrp` | X de Uchoa et al. (`examples/cvrp/uchoa/`) | mejor conocida (CVRPLIB) | todas |
| `clsp` | Trigeiro et al. (`examples/lotsizing/trigeiro/`) | CBC y la tabla 9 de Degraeve y Jans | F; cada G |

Cada réplica de cada corrida (`results/tune_runNN/r<k>/generated.json`) es una configuración; `--extra` agrega otras.
El tiempo es `--budget` segundos por corrida o, en el flow shop, el protocolo de la literatura n·m/2·t ms (`--t`).
Las corridas van en paralelo (`--workers` procesos).
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from random import Random
from statistics import mean
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent / "examples"


def _json(path: Path) -> dict:
    return {k: v for k, v in json.loads(path.read_text()).items() if not k.startswith("_")}


def _trigeiro_reference() -> dict[str, float]:
    """CBC (`cbc.json`) y, en las G, las mejores de la tabla 9 de Degraeve y Jans (`reference.json`)."""
    d = ROOT / "lotsizing" / "trigeiro"
    best = {k: v["ub"] for k, v in _json(d / "cbc.json").items() if v.get("ub") is not None} if (d / "cbc.json").exists() else {}
    for k, v in _json(d / "reference.json").items():
        for key in ("BW_IP", "BP_IP"):
            if key in v:
                best[k] = min(best.get(k, float("inf")), v[key])
    return best


def _pfsp_class(name: str) -> str:
    return "_".join(name[3:].split("_")[:2])


def _pfsp_time(name: str, t: float) -> float:
    n, m = _pfsp_class(name).split("_")
    return int(n) * int(m) / 2 * t / 1000.0


@dataclass
class Bench:
    pack: str  # nombre del problema en core.packs
    dir: Path
    ext: str
    reference: Callable[[], dict[str, float]]
    group: Callable[[str], str]
    protocol: Callable[[str, float], float] | None = None  # (instancia, t) -> segundos


BENCHES = {
    "flowshop": Bench("flowshop", ROOT / "flowshop" / "taillard", ".txt",
                      lambda: _json(ROOT / "flowshop" / "taillard" / "best_known.json"), _pfsp_class, _pfsp_time),
    "flowshop_cmax": Bench("flowshop_cmax", ROOT / "flowshop" / "taillard", ".txt",
                           lambda: _json(ROOT / "flowshop_cmax" / "best_known.json"), _pfsp_class, _pfsp_time),
    "jobshop": Bench("jobshop", ROOT / "jobshop" / "taillard", ".txt",
                     lambda: _json(ROOT / "jobshop" / "taillard" / "best_known.json"),
                     lambda n: "15×15" if int(n[2:]) <= 10 else "20×15"),
    "cvrp": Bench("cvrp", ROOT / "cvrp" / "uchoa", ".vrp", lambda: _json(ROOT / "cvrp" / "uchoa" / "best_known.json"),
                  lambda n: "X"),
    "clsp": Bench("clsp", ROOT / "lotsizing" / "trigeiro", ".txt", _trigeiro_reference,
                  lambda n: "F" if n.startswith("F") else n),
}


def _run(job):
    problem, label, config, name, seed, seconds, generated, mip = job
    from core.packs import base_pack
    from tuning.cli import make_assembler

    b = BENCHES[problem]
    pack = base_pack(b.pack)
    assembler, _ = make_assembler(pack, generated, mip=mip, generated_destructions=True)  # las configuraciones pueden usarlas
    inst = pack.load_instance(str(b.dir / f"{name}{b.ext}"))
    res = assembler.assemble(config)(inst, Random(seed), seconds)
    P = pack.problem_factory(inst)
    return {"config": label, "instance": name, "seed": seed, "seconds": seconds, "cost": P.objective(res.best_solution),
            "feasible": P.is_feasible(res.best_solution), "iterations": res.iterations}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("problem", choices=sorted(BENCHES))
    ap.add_argument("runs", nargs="*", help="directorios results/tune_runNN (una configuración por réplica)")
    ap.add_argument("--generated", default=None, help="workspace de los componentes (default generated/<problema>_native)")
    ap.add_argument("--budget", type=float, default=None, help="segundos por corrida")
    ap.add_argument("--t", type=float, default=None, help="flow shop: n·m/2·t ms por instancia (default 60)")
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--first-seed", type=int, default=0, help="semillas first-seed .. first-seed+seeds-1 (para repartir corridas)")
    ap.add_argument("--instances", nargs="*", default=None, help="prefijos de los nombres (p.ej. G, tai50_10, X-n1); default todas")
    ap.add_argument("--extra", nargs="*", default=[], help="nombre='{config JSON}'")
    ap.add_argument("--best-known", default=None, help="otra referencia del gap (JSON {instancia: costo})")
    ap.add_argument("--mip", choices=["auto", "generated", "reference"], default="auto", help="vista MIP de HYB")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out")
    args = ap.parse_args(argv)

    from core.packs import base_pack
    from scripts.tuning_replicas import load_replicas
    from tuning.cli import make_assembler

    b = BENCHES[args.problem]
    generated = args.generated or f"generated/{b.pack}_native"
    make_assembler(base_pack(b.pack), generated, mip=args.mip, generated_destructions=True)  # compila una vez antes de repartir
    configs: dict[str, tuple[dict, str]] = {}
    for run in args.runs:
        for rep, path in load_replicas(Path(run)):
            payload = json.loads((path / "generated.json").read_text())
            configs[f"{Path(run).name}/{rep}"] = (payload["test"]["tuned"]["config"], payload["test"]["tuned"]["summary"])
    for item in args.extra:
        name, cfg = item.split("=", 1)
        configs[name] = (json.loads(cfg), "extra")
    if not configs:
        raise SystemExit("sin configuraciones: da directorios de corridas o --extra")
    ref = _json(Path(args.best_known)) if args.best_known else b.reference()
    names = sorted(p.stem for p in b.dir.glob(f"*{b.ext}") if p.stem in ref
                   and (not args.instances or any(p.stem.startswith(x) for x in args.instances)))
    if b.protocol is not None and args.budget is None:
        t = args.t or 60.0
        seconds, when = (lambda n: b.protocol(n, t)), f"n·m/2·{t:g} ms"
    else:
        seconds, when = (lambda n: args.budget or 30.0), f"{args.budget or 30.0:g} s"
    seeds = range(args.first_seed, args.first_seed + args.seeds)
    jobs = [(args.problem, label, cfg, n, s, seconds(n), generated, args.mip) for label, (cfg, _) in configs.items() for n in names for s in seeds]
    jobs.sort(key=lambda j: -j[5])  # las largas primero
    with ProcessPoolExecutor(args.workers) as pool:
        rows = list(pool.map(_run, jobs))

    gap = lambda r: 100 * (r["cost"] - ref[r["instance"]]) / ref[r["instance"]]  # noqa: E731
    groups: dict[str, list[str]] = {}
    for n in names:
        groups.setdefault(b.group(n), []).append(n)
    print(f"gap contra la mejor conocida; {when} por corrida; {args.seeds} semilla(s); {len(names)} instancias\n")
    print(f"{'grupo':<10}" + "".join(f"{label[-22:]:>24}" for label in configs))
    for g, members in groups.items():
        cells = [mean(gap(r) for r in rows if r["config"] == label and r["instance"] in members) for label in configs]
        print(f"{g:<10}" + "".join(f"{v:>23.2f}%" for v in cells))
    if len(groups) > 1:
        print(f"{'media':<10}" + "".join(f"{mean(gap(r) for r in rows if r['config'] == label):>23.2f}%" for label in configs))
    for label, (_, summary) in configs.items():
        print(f"  {label}: {summary}")
    bad = [(r["config"], r["instance"]) for r in rows if not r["feasible"]]
    if bad:
        print(f"\nINFACTIBLES: {len(bad)}" + "".join(f"\n  {c} {n}" for c, n in bad[:20]))
    new = sorted({(r["instance"], r["cost"], ref[r["instance"]], r["config"]) for r in rows
                  if r["feasible"] and r["cost"] < ref[r["instance"]] - 1e-6})
    print(f"\nmejores que la referencia: {len({n for n, *_ in new})}" + "".join(f"\n  {n}: {c:.0f} < {b_:.0f} ({l})" for n, c, b_, l in new))
    if args.out:
        Path(args.out).write_text(json.dumps({"problem": args.problem, "time": when, "seeds": list(seeds), "reference": ref,
                                              "configs": {k: v[1] for k, v in configs.items()}, "rows": rows}, indent=1))


if __name__ == "__main__":
    main()
