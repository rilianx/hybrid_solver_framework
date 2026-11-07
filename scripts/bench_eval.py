"""Las configuraciones elegidas por corridas de tuning, en el benchmark de la literatura de cada problema, con el gap
contra la mejor solución conocida (un gap negativo es una mejor solución nueva).

    python -m scripts.bench_eval flowshop results/tune_run75 --t 60 --seeds 3 --out results/pfsp_run75.json
    python -m scripts.bench_eval jobshop results/tune_run83 --budget 30 --seeds 3
    python -m scripts.bench_eval cvrp results/tune_run81 --budget 30 --instances X-n101 X-n1
    python -m scripts.bench_eval clsp results/tune_run79 --budget 60 --instances G --extra base='{"skeleton": "ILS", ...}'

| problema | instancias | referencia | grupos |
|---|---|---|---|
| `flowshop`, `flowshop_cmax` | Taillard (`examples/flowshop/taillard/`) | mejores conocidas de flowtime / makespan | clase n_m |
| `jobshop` | Taillard ta01–ta80 y OR-Library (`examples/jobshop/bench/`) | óptimo o mejor conocida (Weise 2020) | ta por tamaño; abz, ft, la, orb, swv, yn |
| `cvrp` | X de Uchoa et al. (`examples/cvrp/uchoa/`, 100) | mejor conocida (CVRPLIB) | todas |
| `cvrp_frontierco` | CVRP de FrontierCO (`examples/cvrp/frontierco/`): Golden, valid, Arnold | la de FrontierCO | Golden, valid, Arnold |
| `clsp` | Trigeiro et al. (`examples/lotsizing/trigeiro/`) | CBC y la tabla 9 de Degraeve y Jans | F; cada G |
| `mkp` | OR-Library: mknap1, mknap2, mknapcb1–9 (`examples/mkp/orlib/`) | óptimo o mejor conocida (CO-Bench) | archivo |
| `mkp_reevo` | test100–1000 de ReEvo = MKP de MCTS-AHD (`examples/mkp/reevo/`, con `fetch --reevo`) | óptimo (CBC) | tamaño |
| `cvrp_reevo`, `cvrp_mcts_ahd` | test de ReEvo y de MCTS-AHD (`examples/cvrp/reevo/`, `mcts_ahd/`) | HGS (`examples/cvrp/reference.py`) | tamaño |
| `sscflp` | Holmberg, Díaz-Fernández, Yang, TB4, OR-Library y TBED1 (`examples/sscflp/bench/`) | óptimo o mejor conocida | H, D, Y, TB4, cap, capa–c, i300 … i3001500 |

Cada réplica de cada corrida (`results/tune_runNN/r<k>/generated.json`) es una configuración; `--extra` agrega otras.
El tiempo por corrida crece con el tamaño de la instancia (`_PROTOCOLS`, con `--t`): el del flow shop, n·m/2·t ms
(Taillard; Ruiz y Stützle), con el análogo de n·m en cada problema (operaciones, ítems × períodos, centros × clientes,
ítems × restricciones), y en el CVRP n·t/100 s (t = 240 es el 2,4·n s de Vidal 2022, el de PyVRP y el DIMACS). Con
`--budget`, segundos fijos (para compararse con CO-Bench, 10 s, o FrontierCO, hasta 3600 s).
Las corridas van en paralelo (`--workers` procesos).
"""

from __future__ import annotations

import argparse
import json
import re
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from random import Random
from statistics import mean
from typing import Any, Callable

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


def _nm_ms(size: Callable[[Any], int]) -> tuple[Callable[[Any, float], float], str]:
    """El protocolo del flow shop (Taillard; Ruiz y Stützle): size/2·t ms, con size = n·m o el análogo del problema."""
    return (lambda inst, t: size(inst) / 2 * t / 1000.0), "size/2·t ms"


_PROTOCOLS = {  # (instancia, t) -> segundos; t por defecto; descripción
    "flowshop": (*_nm_ms(lambda i: i.n_jobs * i.n_machines), 60.0, "n·m/2·t ms (trabajos × máquinas)"),
    "jobshop": (*_nm_ms(lambda i: i.n_jobs * i.n_machines), 60.0, "n·m/2·t ms (operaciones)"),
    "clsp": (*_nm_ms(lambda i: i.n_items * i.n_periods), 60.0, "N·T/2·t ms (ítems × períodos)"),
    "sscflp": (*_nm_ms(lambda i: i.n_facilities * i.n_customers), 60.0, "n·m/2·t ms (centros × clientes)"),
    "mkp": (*_nm_ms(lambda i: i.n_items * i.n_resources), 60.0, "n·m/2·t ms (ítems × restricciones)"),
    # Vidal (2022), el de PyVRP y el DIMACS en las X: 2,4·n s, que es t = 240
    "cvrp": (lambda i, t: i.n_customers * t / 100.0, "", 240.0, "n·t/100 s (clientes; t = 240 es el 2,4·n s de Vidal 2022)"),
}
_PROTOCOLS["flowshop_cmax"] = _PROTOCOLS["flowshop"]


_TA_SIZES = ["15×15", "20×15", "20×20", "30×15", "30×20", "50×15", "50×20", "100×20"]


def _jssp_group(name: str) -> str:
    """Taillard por tamaño (ta01–10 15×15 … ta71–80 100×20); las de la OR-Library por familia (abz, ft, la, orb, swv, yn)."""
    if re.fullmatch(r"ta\d+", name):
        return "ta " + _TA_SIZES[(int(name[2:]) - 1) // 10]
    return name.rstrip("0123456789")


def _sscflp_group(name: str) -> str:
    """H, D, Y, TB4, cap (16–50 centros), capa/capb/capc, i300, i500, i700, i1000, i3001500."""
    if "-" in name:
        return name.split("-")[0]
    return re.match(r"(cap[abc]?|i\d+)", name).group(1)


@dataclass
class Bench:
    pack: str  # nombre del problema en core.packs
    dir: Path
    ext: str
    reference: Callable[[], dict[str, float]]
    group: Callable[[str], str]

    @property
    def protocol(self):
        """(segundos(instancia, t), t por defecto, descripción): el tiempo crece con el tamaño de la instancia."""
        fn, _, t, text = _PROTOCOLS[self.pack]
        return fn, t, text


BENCHES = {
    "flowshop": Bench("flowshop", ROOT / "flowshop" / "taillard", ".txt",
                      lambda: _json(ROOT / "flowshop" / "taillard" / "best_known.json"), _pfsp_class),
    "flowshop_cmax": Bench("flowshop_cmax", ROOT / "flowshop" / "taillard", ".txt",
                           lambda: _json(ROOT / "flowshop_cmax" / "best_known.json"), _pfsp_class),
    "jobshop": Bench("jobshop", ROOT / "jobshop" / "bench", ".txt",
                     lambda: {k: v["ub"] for k, v in _json(ROOT / "jobshop" / "bench" / "best_known.json").items()},
                     _jssp_group),
    "cvrp": Bench("cvrp", ROOT / "cvrp" / "uchoa", ".vrp", lambda: _json(ROOT / "cvrp" / "uchoa" / "best_known.json"),
                  lambda n: "X"),
    "cvrp_frontierco": Bench("cvrp", ROOT / "cvrp" / "frontierco", ".txt",
                             lambda: _json(ROOT / "cvrp" / "frontierco" / "best_known.json"),
                             lambda n: "Golden" if n.startswith("Golden") else ("valid" if n.startswith("instance") else "Arnold")),
    "mkp": Bench("mkp", ROOT / "mkp" / "orlib", ".txt", lambda: _json(ROOT / "mkp" / "orlib" / "best_known.json"),
                 lambda n: n.split("_")[0]),
    "mkp_reevo": Bench("mkp", ROOT / "mkp" / "reevo", ".txt",
                       lambda: {k: v["ub"] for k, v in _json(ROOT / "mkp" / "reevo_best_known.json").items()},
                       lambda n: n.split("_")[0]),
    "cvrp_reevo": Bench("cvrp", ROOT / "cvrp" / "reevo", ".txt",
                        lambda: {k: v["ub"] for k, v in _json(ROOT / "cvrp" / "reevo" / "best_known.json").items()},
                        lambda n: n.split("_")[0]),
    "cvrp_mcts_ahd": Bench("cvrp", ROOT / "cvrp" / "mcts_ahd", ".txt",
                           lambda: {k: v["ub"] for k, v in _json(ROOT / "cvrp" / "mcts_ahd" / "best_known.json").items()}
                           if (ROOT / "cvrp" / "mcts_ahd" / "best_known.json").exists() else {},
                           lambda n: n.split("_")[0]),
    "sscflp": Bench("sscflp", ROOT / "sscflp" / "bench", ".txt",
                    lambda: {k: v["ub"] for k, v in _json(ROOT / "sscflp" / "bench" / "best_known.json").items()},
                    _sscflp_group),
    "clsp": Bench("clsp", ROOT / "lotsizing" / "trigeiro", ".txt", _trigeiro_reference,
                  lambda n: "F" if n.startswith("F") else n),
}


def _run(job):
    problem, label, config, name, seed, seconds, generated = job
    from core.packs import base_pack
    from tuning.cli import make_assembler

    b = BENCHES[problem]
    pack = base_pack(b.pack)
    assembler, _ = make_assembler(pack, generated, generated_destructions=True)  # las configuraciones pueden usarlas
    inst = pack.load_instance(str(b.dir / f"{name}{b.ext}"))
    res = assembler.assemble(config)(inst, Random(seed), seconds)
    P = pack.problem_factory(inst)
    return {"config": label, "instance": name, "seed": seed, "seconds": seconds, "cost": P.objective(res.best_solution),
            "feasible": P.is_feasible(res.best_solution), "iterations": res.iterations}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("problem", choices=sorted(BENCHES))
    ap.add_argument("runs", nargs="*", help="directorios results/tune_runNN (una configuración por réplica) o de una réplica "
                                            "(results/tune_runNN/r1)")
    ap.add_argument("--generated", default=None, help="workspace de los componentes (default generated/<problema>_native)")
    ap.add_argument("--budget", type=float, default=None,
                    help="segundos fijos por corrida (CO-Bench: 10; FrontierCO: 3600); sin esto, el protocolo del problema")
    ap.add_argument("--t", type=float, default=None,
                    help="t del protocolo: size/2·t ms (default 60) o, en el CVRP, n·t/100 s (default 240, Vidal 2022)")
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--first-seed", type=int, default=0, help="semillas first-seed .. first-seed+seeds-1 (para repartir corridas)")
    ap.add_argument("--instances", nargs="*", default=None, help="prefijos de los nombres (p.ej. G, tai50_10, X-n1); default todas")
    ap.add_argument("--extra", nargs="*", default=[], help="nombre='{config JSON}'")
    ap.add_argument("--best-known", default=None, help="otra referencia del gap (JSON {instancia: costo})")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out")
    ap.add_argument("--merge", nargs="*", default=None,
                    help="no corre nada: junta las salidas --out de varias partes (instancias o semillas repartidas) y "
                         "las resume como una sola")
    args = ap.parse_args(argv)
    if args.merge:
        _merge(args.problem, [Path(f) for f in args.merge], args.out)
        return

    from core.packs import base_pack
    from scripts.tuning_replicas import load_replicas
    from tuning.cli import make_assembler

    b = BENCHES[args.problem]
    generated = args.generated or f"generated/{b.pack}_native"
    make_assembler(base_pack(b.pack), generated, generated_destructions=True)  # compila una vez antes de repartir
    configs: dict[str, tuple[dict, str]] = {}
    for run in args.runs:
        reps = [(Path(run).name, Path(run))] if (Path(run) / "generated.json").exists() else load_replicas(Path(run))
        for rep, path in reps:
            if rep == Path(run).name:  # una réplica sola: tune_runNN/r1
                payload = json.loads((path / "generated.json").read_text())
                configs[f"{path.parent.name}/{rep}"] = (payload["test"]["tuned"]["config"], payload["test"]["tuned"]["summary"])
                continue
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
    if args.budget is None:  # el protocolo del problema: el tiempo crece con el tamaño
        from core.packs import base_pack

        fn, t_default, text = b.protocol
        t = args.t or t_default
        load = base_pack(b.pack).load_instance
        secs = {n: fn(load(str(b.dir / f"{n}{b.ext}")), t) for n in names}
        seconds, when = secs.__getitem__, f"{text} con t = {t:g}"
    else:  # un tiempo fijo (CO-Bench: 10 s por instancia; FrontierCO: hasta 3600 s)
        seconds, when = (lambda n: args.budget), f"{args.budget:g} s"
    seeds = range(args.first_seed, args.first_seed + args.seeds)
    jobs = [(args.problem, label, cfg, n, s, seconds(n), generated) for label, (cfg, _) in configs.items() for n in names for s in seeds]
    jobs.sort(key=lambda j: -j[5])  # las largas primero
    with ProcessPoolExecutor(args.workers) as pool:
        rows = list(pool.map(_run, jobs))

    _report(args.problem, rows, ref, {k: v[1] for k, v in configs.items()}, when, list(seeds), args.out)


def _report(problem: str, rows: list[dict], ref: dict, configs: dict[str, str], when: str, seeds: list[int],
            out: str | None) -> None:
    """La tabla de gaps por grupo y configuración, las infactibles y las mejores que la referencia."""
    b = BENCHES[problem]
    names = sorted({r["instance"] for r in rows})
    # |ref|: en los de maximización (MKP) el costo es el beneficio con signo menos y la referencia es negativa
    gap = lambda r: 100 * (r["cost"] - ref[r["instance"]]) / abs(ref[r["instance"]])  # noqa: E731
    groups: dict[str, list[str]] = {}
    for n in names:
        groups.setdefault(b.group(n), []).append(n)
    print(f"gap contra la mejor conocida; {when} por corrida; {len(seeds)} semilla(s); {len(names)} instancias\n")
    print(f"{'grupo':<10}" + "".join(f"{label[-22:]:>24}" for label in configs))
    for g, members in groups.items():
        cells = [mean(gap(r) for r in rows if r["config"] == label and r["instance"] in members) for label in configs]
        print(f"{g:<10}" + "".join(f"{v:>23.2f}%" for v in cells))
    if len(groups) > 1:
        print(f"{'media':<10}" + "".join(f"{mean(gap(r) for r in rows if r['config'] == label):>23.2f}%" for label in configs))
    for label, summary in configs.items():
        print(f"  {label}: {summary}")
    bad = [(r["config"], r["instance"]) for r in rows if not r["feasible"]]
    if bad:
        print(f"\nINFACTIBLES: {len(bad)}" + "".join(f"\n  {c} {n}" for c, n in bad[:20]))
    new = sorted({(r["instance"], r["cost"], ref[r["instance"]], r["config"]) for r in rows
                  if r["feasible"] and r["cost"] < ref[r["instance"]] - 1e-6})
    print(f"\nmejores que la referencia: {len({n for n, *_ in new})}" + "".join(f"\n  {n}: {c:.0f} < {b_:.0f} ({l})" for n, c, b_, l in new))
    if out:
        Path(out).write_text(json.dumps({"problem": problem, "time": when, "seeds": seeds, "reference": ref,
                                         "configs": configs, "rows": rows}, indent=1))


def _merge(problem: str, files: list[Path], out: str | None) -> None:
    parts = [json.loads(f.read_text()) for f in files]
    if not parts:
        raise SystemExit("--merge sin archivos")
    times = {p["time"] for p in parts}
    if len(times) > 1:
        raise SystemExit(f"las partes tienen protocolos de tiempo distintos: {sorted(times)}")
    rows = [r for p in parts for r in p["rows"]]
    ref = {k: v for p in parts for k, v in p["reference"].items()}
    configs = {k: v for p in parts for k, v in p["configs"].items()}
    seeds = sorted({s for p in parts for s in p["seeds"]})
    _report(problem, rows, ref, configs, times.pop(), seeds, out)


if __name__ == "__main__":
    main()
