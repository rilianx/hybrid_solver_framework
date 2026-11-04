"""Configuración automática en tres etapas (`--tuner staged`): primero la estructura, después los números.

Afinar esqueleto, componentes y parámetros en un solo espacio con irace repartía el presupuesto entre estructuras muy
distintas, y el resultado dependía de la réplica (en el CLSP el HYB con sus defaults le ganó a los HYB afinados; en el
job shop irace dejó de elegir PR). Aquí:

1. **Carrera estructural.** El default de cada esqueleto, una variante por cada componente alternativo de cada slot
   (`evaluation.one_slot_baselines`) y, por esqueleto, la combinación "codiciosa" con el mejor componente de cada
   slot; cada una en las instancias de entrenamiento con sus parámetros por defecto (en paralelo, con el
   target-runner de irace). Quedan las `top` mejores estructuras.
2. **irace en el espacio reducido**: solo los esqueletos y componentes de esas estructuras, partiendo de ellas como
   configuraciones iniciales (`configurationsFile`), así nunca termina peor que un default.
3. **Validación final**: las élites de irace y las estructuras de la etapa 1, en las instancias de entrenamiento con
   `seeds` semillas nuevas; gana la de menor costo medio.
"""

from __future__ import annotations

import json
import shlex
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from statistics import mean
from typing import Any

from config_space.irace_export import to_irace_parameters
from config_space.space import Condition, ConfigSpace

FAILED = 1e12


# ---------------------------------------------------------------------------------------------------- espacio
def unfold(space: ConfigSpace, config: dict[str, Any]) -> dict[str, Any]:
    """Configuración del ensamblador → asignación por nombre de nodo (la inversa de `ConfigSpace.fold`), solo los
    nodos activos."""
    out: dict[str, Any] = {}
    for node in space.nodes:
        if node.config_key in config and node.is_active(out):
            out[node.name] = config[node.config_key]
    return out


def restrict(space: ConfigSpace, allowed: dict[str, set]) -> ConfigSpace:
    """El espacio con los categóricos de `allowed` limitados a esos valores; caen los nodos cuyas condiciones ya no se
    pueden cumplir (parámetros de componentes descartados)."""
    out = ConfigSpace()
    domain: dict[str, tuple] = {}
    for node in space.nodes:
        conds = []
        ok = True
        for c in node.conditions:
            if c.parent not in domain:
                ok = False
                break
            vals = tuple(v for v in c.values if v in domain[c.parent])
            if not vals:
                ok = False
                break
            conds.append(Condition(c.parent, c.kind if len(vals) == len(c.values) or c.kind == "in" else "in", vals))
        if not ok:
            continue
        values = node.values
        if node.type == "cat" and node.name in allowed:
            values = tuple(v for v in node.values if v in allowed[node.name])
            if not values:
                continue
        new = replace(node, values=values, conditions=tuple(conds))
        out.add(new)
        domain[node.name] = values if node.type in ("cat", "bool") else ()
    return out


def irace_args(space: ConfigSpace, config: dict[str, Any]) -> list[str]:
    return [f"--{k}={v}" for k, v in unfold(space, config).items()]


def write_configurations(space: ConfigSpace, configs: list[dict[str, Any]], path: Path) -> None:
    """`configurationsFile` de irace: una fila por configuración, NA en los parámetros inactivos."""
    names = [n.name for n in space.nodes]
    rows = [" ".join(names)]
    for cfg in configs:
        a = unfold(space, cfg)
        rows.append(" ".join(json.dumps(str(a[n])) if n in a and isinstance(a[n], str) else str(a.get(n, "NA")) for n in names))
    path.write_text("\n".join(rows) + "\n")


# ---------------------------------------------------------------------------------------------------- evaluación
def evaluate_many(runner: Path, space: ConfigSpace, configs: list[dict[str, Any]], instances: list[Path],
                  seeds: list[int], parallel: int) -> list[list[float]]:
    """Costo de cada configuración en cada (instancia, semilla), con el target-runner del escenario (el mismo
    presupuesto, objetivo y backend que irace), `parallel` corridas a la vez."""
    jobs = [(c, i, s) for c in range(len(configs)) for i in range(len(instances)) for s in seeds]

    def one(job):
        c, i, s = job
        cmd = [str(runner), str(c + 1), str(i + 1), str(s), str(instances[i]), *irace_args(space, configs[c])]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=runner.parent, timeout=3600)
            return float(proc.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError, subprocess.TimeoutExpired):
            return FAILED

    with ThreadPoolExecutor(max(1, parallel)) as pool:
        costs = list(pool.map(one, jobs))
    out = [[] for _ in configs]
    for (c, _i, _s), v in zip(jobs, costs):
        out[c].append(v)
    return out


# ---------------------------------------------------------------------------------------------------- etapas
def structural_candidates(assembler, skeletons: list[str] | None = None) -> dict[str, dict[str, Any]]:
    from tuning.evaluation import one_slot_baselines

    return one_slot_baselines(assembler, skeletons)


def greedy_structures(assembler, scores: dict[str, float]) -> dict[str, dict[str, Any]]:
    """Por esqueleto, el default con el componente de mejor puntaje en cada slot (las variantes de un componente se
    llaman `SK:slot=nombre`)."""
    out = {}
    for sk in assembler.available_skeletons():
        base = scores.get(f"default:{sk}")
        if base is None:
            continue
        choices = {}
        for label, v in scores.items():
            if label.startswith(f"{sk}:") and v < base:
                slot, name = label.split(":", 1)[1].split("=", 1)
                if slot not in choices or v < scores[f"{sk}:{slot}={choices[slot]}"]:
                    choices[slot] = name
        if len(choices) >= 2:  # con uno solo ya es una de las variantes
            out[f"greedy:{sk}"] = assembler.default_config(sk, choices)
    return out


def run_staged(assembler, scenario: Path, train_paths: list[Path], budget: float, max_experiments: int, *,
               seed: int = 0, top: int = 2, parallel: int = 4, final_seeds: int = 3, normalizers=None,
               skeletons: list[str] | None = None, log=print):
    from tuning.irace_runner import IraceResult, tune_with_irace

    t0 = time.monotonic()
    scenario = Path(scenario).resolve()
    root, runner = scenario.parent, scenario.parent / "target-runner"
    space = assembler.config_space()
    report: dict[str, Any] = {}

    # 1. carrera estructural
    cands = structural_candidates(assembler, skeletons)
    costs = evaluate_many(runner, space, list(cands.values()), train_paths, [seed], parallel)
    scores = {label: mean(c) for label, c in zip(cands, costs)}
    greedy = greedy_structures(assembler, scores)
    if greedy:
        gcosts = evaluate_many(runner, space, list(greedy.values()), train_paths, [seed], parallel)
        scores.update({label: mean(c) for label, c in zip(greedy, gcosts)})
        cands.update(greedy)
    ranked = sorted(scores, key=scores.get)
    # las `top` mejores estructuras de esqueletos distintos (dos variantes casi iguales del mismo esqueleto no le dan
    # nada a irace)
    chosen, seen = [], set()
    for label in ranked:
        sk = cands[label]["skeleton"]
        if sk not in seen:
            chosen.append(label)
            seen.add(sk)
        if len(chosen) == top:
            break
    report["screen"] = {label: round(scores[label], 6) for label in ranked}
    report["chosen"] = chosen
    log(f"  etapa 1 (estructura): {len(scores)} variantes; elegidas: "
        + "; ".join(f"{label} = {scores[label]:.4f}" for label in chosen))
    exps = len(scores) * len(train_paths)

    # 2. irace en el espacio de esas estructuras, partiendo de ellas
    # por slot, los componentes de las estructuras elegidas y los que en la etapa 1 no fueron peores que el default de
    # su esqueleto
    allowed: dict[str, set] = {}
    slot_nodes = {n.name for n in space.nodes if n.type == "cat" and "." not in n.name}
    for label in chosen:
        sk = cands[label]["skeleton"]
        for name, value in unfold(space, cands[label]).items():
            if name in slot_nodes:
                allowed.setdefault(name, set()).add(value)
        base = scores.get(f"default:{sk}", float("inf"))
        for other, v in scores.items():
            if other.startswith(f"{sk}:") and v <= base:
                for name, value in unfold(space, cands[other]).items():
                    if name in slot_nodes and name != "skeleton":
                        allowed.setdefault(name, set()).add(value)
    small = restrict(space, allowed)
    (root / "parameters.txt").write_text(to_irace_parameters(small))
    write_configurations(small, [cands[label] for label in chosen], root / "configurations.txt")
    text = scenario.read_text()
    if "configurationsFile" not in text:
        scenario.write_text(text + 'configurationsFile = "./configurations.txt"\n')
    log(f"  etapa 2 (irace): {len(small.nodes)} de {len(space.nodes)} parámetros")
    res = tune_with_irace(assembler, scenario, [], budget, max_experiments, seed=seed, normalizers=normalizers,
                          parallel=parallel, evaluate_best=False)
    exps += res.experiments

    # 3. validación final con semillas nuevas
    finalists = {f"irace#{k}": cfg for k, cfg in enumerate(res.elites[:3])}
    finalists.update({label: cands[label] for label in chosen})
    fseeds = [seed + 1000 + k for k in range(final_seeds)]
    fcosts = evaluate_many(runner, space, list(finalists.values()), train_paths, fseeds, parallel)
    final = {label: mean(c) for label, c in zip(finalists, fcosts)}
    best = min(final, key=final.get)
    exps += len(finalists) * len(train_paths) * len(fseeds)
    report["final"] = {label: round(v, 6) for label, v in sorted(final.items(), key=lambda kv: kv[1])}
    report["best"] = best
    log("  etapa 3 (validación, " + f"{final_seeds} semillas): " + "; ".join(f"{label} = {v:.4f}" for label, v in
                                                                              sorted(final.items(), key=lambda kv: kv[1])))
    (root / "staged.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    elites = [finalists[best]] + [c for label, c in finalists.items() if label != best]
    return IraceResult(finalists[best], elites, final[best], time.monotonic() - t0, exps,
                       [f"staged: {shlex.quote(best)}"] + res.log_tail[-20:])


__all__ = ["evaluate_many", "greedy_structures", "irace_args", "restrict", "run_staged", "unfold", "write_configurations"]
