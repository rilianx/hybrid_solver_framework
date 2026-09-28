"""Por qué un catálogo le gana a otro: las configuraciones elegidas por dos corridas de tuning, en
las mismas instancias de test y la misma máquina, con varios presupuestos, contando lo que hace
cada una (iteraciones del esqueleto y llamadas a los métodos de sus componentes).

Si la brecha se cierra con más tiempo, la diferencia es de velocidad; si se mantiene, es de la
búsqueda (qué movimientos, qué constructor, qué esqueleto).

    python -m scripts.diagnose_gap --budgets 1.25 2.5 5 10 20 --out diag.json \\
        --side mano:results/tune_run30:handwritten:cvrp:: \\
        --side gen:results/tune_run35:generated:cvrp:tour:generated/cvrp_tour_cycle2 \\
        --side gen_refmodel:results/tune_run35:generated:cvrp:tour:generated/cvrp_tour_cycle2:ref

Cada `--side` es `nombre:corrida:catálogo:problema:variante:workspace[:ref]`; `ref` usa el modelo de
referencia de la variante con los componentes del workspace (separa modelo de componentes).
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path
from random import Random
from statistics import mean

COUNTED = ("delta", "moves", "apply", "perturb", "destroy", "score", "build")


class _Counting:
    """Proxy de un componente que cuenta llamadas a sus métodos."""

    def __init__(self, impl, counter: Counter, slot: str):
        object.__setattr__(self, "_impl", impl)
        object.__setattr__(self, "_counter", counter)
        object.__setattr__(self, "_slot", slot)

    def __getattr__(self, name):
        attr = getattr(self._impl, name)
        if name in COUNTED and callable(attr):
            counter, key = self._counter, f"{self._slot}.{name}"

            def wrapped(*a, **k):
                counter[key] += 1
                return attr(*a, **k)

            return wrapped
        return attr


def _side(spec: str):
    parts = spec.split(":")
    name, run, catalog, problem, variant, workspace = parts[:6]
    ref = len(parts) > 6 and parts[6] == "ref"
    if variant:
        from llm.cycle import load_variant

        pack = load_variant(problem, variant, workspace or None, reference=ref)
    else:
        from llm.cycle import base_pack

        pack = base_pack(problem)
    reps = [json.loads((p / f"{catalog}.json").read_text()) for p in sorted(Path(run).glob("r[0-9]"))]
    return name, pack, catalog, workspace or None, reps


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--side", action="append", required=True)
    ap.add_argument("--budgets", type=float, nargs="+", default=[1.25, 2.5, 5, 10, 20])
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from core.component import ComponentSpec  # noqa: F401 — asegura el import antes de parchear
    from tuning.cli import make_assembler

    sides = [_side(s) for s in args.side]
    s = sides[0][4][0]["settings"]
    pack0 = sides[0][1]
    test = pack0.make_instances(s["test"], 500 + s["seed"] * 1000, pack0.parse_size(str(s["size"])))
    bk = [min(x) for x in zip(*[r["test"]["best_known"] for _, _, _, _, reps in sides for r in reps])]
    out = {"best_known": bk, "budgets": args.budgets, "sides": {}}
    for name, pack, catalog, ws, reps in sides:
        assembler, _ = make_assembler(pack, catalog, ws, skeletons=s["skeletons"] if s["skeletons"] != "all" else None)
        counter: Counter = Counter()
        _instrument(assembler.registry, counter)
        rows = []
        from core.assembler import AssemblyError

        for k, r in enumerate(reps):
            cfg = r["test"]["tuned"]["config"]
            try:
                assembler.assemble(cfg)
            except AssemblyError as exc:  # p.ej. un puntaje que depende de la vista constructiva de otro modelo
                print(f"{name} r{k}: se omite ({exc})", flush=True)
                continue
            for b in args.budgets:
                for i, inst in enumerate(test):
                    for seed in range(args.seeds):
                        counter.clear()
                        runner = assembler.assemble(cfg)
                        t0 = time.perf_counter()
                        res = runner(inst, Random(seed + i), b)
                        wall = time.perf_counter() - t0
                        ok = pack.problem_factory(inst).is_feasible(res.best_solution)
                        rows.append({"replica": k, "budget": b, "instance": i, "seed": seed, "cost": res.best_objective,
                                     "feasible": ok, "gap": (res.best_objective - bk[i]) / bk[i], "iterations": res.iterations,
                                     "wall": wall, "calls": dict(counter)})
                g = [x["gap"] for x in rows if x["replica"] == k and x["budget"] == b]
                print(f"{name} r{k} {b:>5}s gap {mean(g):.2%}  {r['test']['tuned']['summary']}", flush=True)
        out["sides"][name] = {"configs": [r["test"]["tuned"]["summary"] for r in reps], "rows": rows}
        Path(args.out).write_text(json.dumps(out))
    print(_summary(out))


def _instrument(registry, counter: Counter) -> None:
    """Envuelve la fábrica de cada componente registrado para contar llamadas."""
    for slot, specs in _specs_by_slot(registry).items():
        for spec in specs:
            factory = spec.impl
            if getattr(factory, "_counting", False):
                continue

            def make(*a, _f=factory, _slot=slot, **k):
                return _Counting(_f(*a, **k), counter, _slot)

            make._counting = True  # type: ignore[attr-defined]
            object.__setattr__(spec, "impl", make)


def _specs_by_slot(registry) -> dict:
    slots = {}
    for slot in ("neighborhood", "perturbation", "destruction", "constructor", "greedy_score", "fixing_policy"):
        try:
            slots[slot] = list(registry.for_slot(slot))
        except Exception:  # noqa: BLE001
            continue
    return slots


def _summary(out: dict) -> str:
    lines = []
    for name, side in out["sides"].items():
        for b in out["budgets"]:
            rows = [r for r in side["rows"] if r["budget"] == b]
            calls = Counter()
            for r in rows:
                calls.update(r["calls"])
            per_s = {k: v / sum(r["wall"] for r in rows) for k, v in calls.items()}
            lines.append(f"{name:>13} {b:>5}s gap {mean(r['gap'] for r in rows):6.2%}  iter/s "
                         f"{sum(r['iterations'] for r in rows) / sum(r['wall'] for r in rows):9,.0f}  "
                         + "  ".join(f"{k} {v:,.0f}/s" for k, v in sorted(per_s.items())))
    return "\n".join(lines)


if __name__ == "__main__":
    main()
