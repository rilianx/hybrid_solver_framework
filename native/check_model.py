"""Validar un modelo C++ escrito por el LLM (`native/include/hsf/generic.hpp`) en un proceso aparte (como
`native.check` para los componentes: si el código se cae, la generación no se cae con él).

    python -m native.check_model pedido.json      # imprime el reporte como JSON en la última línea

1. Los casos del problema (visibles y ocultos), con el validador de los modelos por piezas (`check_heuristic_view`).
2. Casos ocultos generados: en instancias del generador del problema (micro y de tamaño realista), las mismas
   violaciones y el mismo costo que las piezas de Python del problema, en la solución trivial, en soluciones al azar y
   en soluciones rotas.
3. Coherencia: `objective` = costo + `penalty` · violaciones, `feasible` sin violaciones y `penalty` como en
   `PartsModel`.
Y mide cuántas evaluaciones del objetivo por segundo hace (va al reporte; no rechaza).
"""

from __future__ import annotations

import importlib
import json
import math
import sys
import time
from pathlib import Path
from random import Random

from core.model_parts import TOL


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-6)


def _viol(d: dict) -> dict:
    return {k: float(v) for k, v in d.items() if float(v) > TOL}


def _dict_close(a: dict, b: dict) -> bool:
    return set(a) == set(b) and all(_close(a[k], b[k]) for k in a)


def _broken(sol, rng: Random) -> list:
    """Soluciones rotas a partir de una buena: un valor cambiado, una fila acortada, una fila de más."""
    rows = [list(r) for r in sol]
    out = []
    if rows and rows[0]:
        a = [list(r) for r in rows]
        i = rng.randrange(len(a))
        if a[i]:
            k = rng.randrange(len(a[i]))
            a[i][k] = a[i][k] + 1 if isinstance(a[i][k], int) and not isinstance(a[i][k], bool) else (not a[i][k])
            out.append(a)
        b = [list(r) for r in rows]
        b[0] = b[0][:-1]
        out.append(b)
    return out


def generated_cases(native, ref, pack, report_cases: int = 3) -> list[str]:
    """Las diferencias con las piezas de Python en instancias del generador (lista vacía si no hay)."""
    from native.generated import ModelCache

    model_of = ModelCache(native)
    sizes = [pack.micro_size or pack.default_size, pack.default_size]
    problems = []
    for size in sizes:
        for k, inst in enumerate(pack.make_instances(2, 900 + 7 * len(problems), pack.parse_size(size))):
            m = model_of(inst)
            rng = Random(k)
            sols = [ref.trivial_solution(inst)] + [ref.random_solution(inst, Random(s)) for s in range(6)]
            sols += [ref.canonical(native.random_solution(m, s)) for s in range(3)]
            sols += [b for s in sols[:4] for b in _broken(s, rng)]
            for sol in sols:
                try:
                    want_v, want_c = _viol(ref.violations(inst, sol)), ref.cost_terms(inst, sol)
                except Exception:  # noqa: BLE001 — la referencia no admite esta solución rota: no es un caso
                    continue
                try:
                    got_v, got_c = _viol(native.violations(m, sol)), native.cost_terms(m, sol)
                except Exception as exc:  # noqa: BLE001
                    problems.append(f"en una instancia oculta de tamaño {size} el modelo lanzó {type(exc).__name__}: {exc}")
                    break
                if not _dict_close(want_v, got_v) or not _dict_close(want_c, got_c):
                    shown = f" (solución {json.dumps(sol)[:300]})" if size == sizes[0] else ""
                    problems.append(f"en una instancia oculta de tamaño {size}{shown}: se esperaban violaciones {want_v} y "
                                    f"costo {want_c}; el modelo dio {got_v} y {got_c}")
                    break
            if len(problems) >= report_cases:
                return problems
    return problems


def coherence(native, ref, pack) -> list[str]:
    from native.generated import ModelCache

    model_of = ModelCache(native)
    out = []
    for inst in pack.make_instances(2, 31, pack.parse_size(pack.default_size)):
        m = model_of(inst)
        triv = ref.trivial_solution(inst)
        want_pen = 10.0 * (abs(sum(ref.cost_terms(inst, triv).values())) + 1.0)
        if not _close(native.penalty(m), want_pen):
            out.append(f"penalty = {native.penalty(m):g}; se espera 10 · (|costo de la trivial| + 1) = {want_pen:g}")
            return out
        for s in [triv] + [ref.random_solution(inst, Random(k)) for k in range(5)]:
            v, c = native.violations(m, s), native.cost_terms(m, s)
            want = sum(c.values()) + native.penalty(m) * sum(v.values())
            if not _close(m.objective(s), want):
                out.append(f"objective = {m.objective(s):g} pero costo + penalty · violaciones = {want:g}")
                return out
            if m.feasible(s) != (not _viol(v)):
                out.append(f"feasible = {m.feasible(s)} con violaciones {v}")
                return out
    return out


def speed(native, ref, pack, seconds: float = 0.5) -> float:
    inst = pack.make_instances(1, 77, pack.parse_size(pack.bench_size or pack.default_size))[0]
    m = native.parse(inst.to_text())
    sols = [ref.random_solution(inst, Random(s)) for s in range(8)]
    return native.bench_objective(m, sols, seconds)


def equivalence(old, new, ref, pack) -> list[str]:
    """Las mismas salidas que el modelo aceptado: violaciones, costo, objetivo, factibilidad y la trivial."""
    from native.generated import ModelCache

    mo, mn = ModelCache(old), ModelCache(new)
    for size in [pack.micro_size or pack.default_size, pack.default_size, pack.bench_size or pack.default_size]:
        for k, inst in enumerate(pack.make_instances(2, 400, pack.parse_size(size))):
            a, b = mo(inst), mn(inst)
            if ref.canonical(old.trivial_solution(a)) != ref.canonical(new.trivial_solution(b)):
                return [f"trivial cambió en una instancia de tamaño {size}"]
            rng = Random(k)
            sols = [ref.random_solution(inst, Random(s)) for s in range(8)] + [old.random_solution(a, s) for s in range(4)]
            sols += [x for s in sols[:4] for x in _broken(s, rng)]
            for s in sols:
                try:
                    want = (old.violations(a, s), old.cost_terms(a, s), a.objective(s), a.feasible(s))
                except Exception:  # noqa: BLE001 — el aceptado no admite esta solución rota
                    continue
                try:
                    got = (new.violations(b, s), new.cost_terms(b, s), b.objective(s), b.feasible(s))
                except Exception as exc:  # noqa: BLE001
                    return [f"lanzó {type(exc).__name__}: {exc} en una solución que el modelo aceptado evalúa"]
                if not (_dict_close(_viol(want[0]), _viol(got[0])) and _dict_close(want[1], got[1]) and _close(want[2], got[2])
                        and want[3] == got[3]):
                    shown = f" (solución {json.dumps(s)[:200]})" if size == (pack.micro_size or pack.default_size) else ""
                    return [f"en una instancia de tamaño {size}{shown}: el aceptado da violaciones {want[0]}, costo {want[1]}, "
                            f"objetivo {want[2]:g}, factible {want[3]}; tu versión da {got[0]}, {got[1]}, {got[2]:g}, {got[3]}"]
    return []


MODEL_METRICS = {"objective": "evaluaciones del objetivo por segundo (soluciones nuevas en cada pasada)",
                 "walk": "pasos por segundo de una trayectoria con los vecindarios del catálogo (media geométrica)"}


def model_speeds(native, ref, pack, neighborhoods: list[str], seconds: float = 0.5) -> dict[str, float]:
    inst = pack.make_instances(1, 77, pack.parse_size(pack.bench_size or pack.default_size))[0]
    m = native.parse(inst.to_text())
    sols = [ref.random_solution(inst, Random(s)) for s in range(8)]
    out = {"objective": native.bench_objective(m, sols, seconds)}
    if neighborhoods:
        rates = [max(native.bench(m, "neighborhood_walk", n, {}, sols, seconds), 1e-9) for n in neighborhoods]
        out["walk"] = math.exp(sum(math.log(r) for r in rates) / len(rates))
    return out


def optimize_check(request: dict) -> dict:
    """Una versión más rápida del modelo aceptado: los mismos chequeos, las mismas salidas y al menos `min_speedup`
    veces más rápida en alguna medida (la trayectoria pide el 40 % de esa mejora; ninguna empeora más de un 10 %)."""
    from core.validation.model_parts import check_heuristic_view
    from llm.cycle import base_pack
    from native.check import thresholds
    from native.generated import load
    from native.generic_model import model_parts

    pack = base_pack(request["problem"])
    old, new = load(request["old_so"], request["old_module"]), load(request["so"], request["module"])
    ref = importlib.import_module(request["mip_parts"])
    out = {"passed": False, "failed_layer": "", "feedback": ""}
    rep = check_heuristic_view(model_parts(new, ref), pack.load_cases())
    if not rep.passed:
        return dict(out, failed_layer="cases", feedback=rep.feedback())
    for layer, problems in (("equivalence", equivalence(old, new, ref, pack)), ("coherence", coherence(new, ref, pack))):
        if problems:
            return dict(out, failed_layer=layer, feedback="\n- ".join(["Las salidas no son las del modelo aceptado:"] + problems))
    nbhs = request.get("neighborhoods", [])
    before, after = model_speeds(old, ref, pack, nbhs), model_speeds(new, ref, pack, nbhs)
    ratios = {k: after[k] / max(before[k], 1e-9) for k in before}
    need = thresholds(before, request.get("min_speedup", 1.5))
    out.update(before=before, after=after)
    detail = "; ".join(f"{MODEL_METRICS[k]}: {before[k]:,.0f} → {after[k]:,.0f} ({ratios[k]:.2f}×, se pide {need[k]:g}×)"
                       for k in before)
    if not any(ratios[k] >= need[k] for k in before) or min(ratios.values()) < 0.9:
        return dict(out, failed_layer="speed", feedback=f"mismas salidas, pero no alcanza: {detail}. Se pide que alguna medida "
                                                        "mejore lo indicado y que ninguna empeore más de un 10 %.")
    return dict(out, passed=True, feedback=detail)


def main(path: str) -> None:
    from core.validation.model_parts import check_heuristic_view
    from llm.cycle import base_pack
    from native.generated import load
    from native.generic_model import model_parts

    request = json.loads(Path(path).read_text())
    if request.get("mode") == "optimize":
        print(json.dumps(optimize_check(request)))
        return
    pack = base_pack(request["problem"])
    native = load(request["so"], request["module"])
    ref = importlib.import_module(request["mip_parts"])
    parts = model_parts(native, ref)
    out = {"passed": False, "failed_layer": "", "feedback": ""}
    rep = check_heuristic_view(parts, pack.load_cases())
    if not rep.passed:
        out.update(failed_layer="cases", feedback=rep.feedback())
        print(json.dumps(out))
        return
    diff = generated_cases(native, ref, pack)
    if diff:
        out.update(failed_layer="hidden_cases", feedback="Difiere de lo esperado en casos ocultos generados:\n- " + "\n- ".join(diff))
        print(json.dumps(out))
        return
    bad = coherence(native, ref, pack)
    if bad:
        out.update(failed_layer="coherence", feedback="Incoherencia entre los métodos del modelo:\n- " + "\n- ".join(bad))
        print(json.dumps(out))
        return
    t0 = time.perf_counter()
    rate = speed(native, ref, pack)
    out.update(passed=True, feedback=f"todos los casos (visibles, ocultos y generados) y la coherencia pasaron; "
                                     f"{rate:,.0f} evaluaciones del objetivo por segundo", objective_rate=rate,
               seconds=round(time.perf_counter() - t0, 2))
    print(json.dumps(out))


def run_model_check(request: dict, timeout: float = 900.0) -> dict:
    import signal
    import subprocess

    req = Path(request["out_dir"]) / "check_model.json"
    req.write_text(json.dumps(request))
    try:
        proc = subprocess.run([sys.executable, "-W", "ignore", "-m", "native.check_model", str(req)], capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"passed": False, "failed_layer": "operational", "feedback": f"la validación no terminó en {timeout:g} s"}
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("{")]
    if proc.returncode == 0 and lines:
        return json.loads(lines[-1])
    why = (f"el proceso terminó con la señal {signal.Signals(-proc.returncode).name}" if proc.returncode < 0
           else f"la validación terminó con código {proc.returncode}")
    return {"passed": False, "failed_layer": "operational", "feedback": f"{why}. Salida de error (final):\n{proc.stderr[-2500:]}"}


if __name__ == "__main__":
    main(sys.argv[1])
