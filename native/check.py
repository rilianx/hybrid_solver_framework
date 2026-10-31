"""Validar un componente C++ generado en un proceso aparte: si el código generado se cae (segfault, abort
por un índice fuera de rango con `_GLIBCXX_ASSERTIONS`), el proceso que genera no se cae con él.

    python -m native.check pedido.json      # imprime el reporte como JSON en la última línea

El pedido trae el problema, el .so ya compilado (con el candidato y los aceptados del mismo slot, que son
los pares de la diversidad) y el nombre del candidato. Las capas son las de Python
(`llm.generator.validate_factory`), sobre los micro-contextos de las piezas nativas del problema.
"""

from __future__ import annotations

import importlib
import json
import signal
import subprocess
import sys
from pathlib import Path

NATIVE_SKELETONS_FOR_SLOT = {"constructor": ["SA", "ILS", "TS", "VNS"], "greedy_score": ["SA", "ILS", "TS", "VNS"],
                             "neighborhood": ["SA", "ILS", "TS", "VNS"], "perturbation": ["ILS"]}


def run_check(request: dict, timeout: float = 900.0) -> dict:
    """Corre la validación en un subproceso; una caída es un rechazo con la señal y la salida de error."""
    req = Path(request["out_dir"]) / f"check_{request['candidate']}.json"
    req.write_text(json.dumps(request))
    try:
        proc = subprocess.run([sys.executable, "-W", "ignore", "-m", "native.check", str(req)], capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"passed": False, "failed_layer": "operational",
                "feedback": f"la validación no terminó en {timeout:g} s: algún método no termina o es demasiado lento"}
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("{")]
    if proc.returncode == 0 and lines:
        return json.loads(lines[-1])
    if proc.returncode < 0:
        sig = signal.Signals(-proc.returncode).name
        why = f"el proceso terminó con la señal {sig} mientras se validaba el componente"
    else:
        why = f"la validación terminó con código {proc.returncode}"
    return {"passed": False, "failed_layer": "operational",
            "feedback": f"componente '{request['candidate']}': {why}. Salida de error (final):\n{proc.stderr[-2500:]}"}


def main(path: str) -> None:
    request = json.loads(Path(path).read_text())
    if request.get("mode") == "optimize":
        return optimize_check(request)
    from llm.cycle import base_pack, parts_contexts
    from llm.generator import validate_factory
    from native.generated import factory, load, parts_for

    pack = base_pack(request["problem"])
    gen = importlib.import_module(pack.native_module).GENERATION
    mod = load(request["so"], request["module"])
    parts = parts_for(mod, importlib.import_module(gen["mip_parts"]))
    contexts = parts_contexts(pack, parts, strict=request.get("strict", True), reference_free=True)
    cand = request["candidate"]
    comp = dict(request["component"])
    comp["compatible_skeletons"] = NATIVE_SKELETONS_FOR_SLOT[comp["slot"]]
    probe = contexts[0].diversity_probe
    peer_problem = probe.problem if probe is not None else contexts[0].problem
    peers = [(name, factory(mod, parts.model, comp["slot"], name)(peer_problem)) for name in request.get("peers", [])]
    report = validate_factory(comp, factory(mod, parts.model, comp["slot"], cand), contexts, peers)
    print(json.dumps({"passed": report.passed, "failed_layer": report.failed_layer, "feedback": report.feedback(),
                      "component": comp}))


def bench_solutions(pack, n: int = 6, seed: int = 4242):
    """Soluciones al azar de una instancia de tamaño realista, donde se mide la velocidad."""
    from random import Random

    gen = importlib.import_module(pack.native_module).GENERATION
    mip = importlib.import_module(gen["mip_parts"])
    inst = pack.make_instances(1, seed, pack.parse_size(pack.default_size))[0]
    return inst, [mip.random_solution(inst, Random(s)) for s in range(n)]


METRICS = {"delta": "delta exacto por segundo (búsqueda local, SA)",
           "ts_step": "candidatos revisados por segundo en un paso de TS (estimate o delta de todos, delta de los 5 mejores)",
           "walk": "pasos por segundo de una trayectoria (revisar los candidatos como en TS, aplicar uno y seguir desde la "
                   "solución que devolvió apply)",
           "perturbation": "perturbaciones por segundo", "greedy_score": "construcciones greedy completas por segundo"}


def thresholds(before: dict, min_speedup: float) -> dict[str, float]:
    """Cuánto tiene que mejorar cada medida para aceptar. La trayectoria también paga lo que no cambia (estimate,
    apply, la revisión del paso), así que una mejora real se ve más chica ahí: se pide el 40 % de la mejora (1,2× si
    a las demás se les pide 1,5×)."""
    return {m: 1 + 0.4 * (min_speedup - 1) if m == "walk" else min_speedup for m in before}


def profile(native, model_of, slot: str, name: str, inst, sols, seconds: float = 0.5) -> str:
    """Dónde se va el tiempo de un vecindario, como texto para el prompt (vacío en otros slots)."""
    if slot != "neighborhood":
        return ""
    p = native.profile_neighborhood(model_of(inst), name, {}, sols, seconds)
    parts = [f"{p['moves_per_solution']:.0f} movimientos por solución", f"moves(s): {p['moves_us_per_solution']:.2f} µs por solución",
             f"delta: {p['delta_us']:.3f} µs por movimiento"]
    if "estimate_us" in p:
        parts.append(f"estimate: {p['estimate_us']:.3f} µs por movimiento")
    parts.append(f"apply: {p['apply_us']:.3f} µs")
    return "; ".join(parts)


def speeds(native, model_of, slot: str, name: str, inst, sols, seconds: float = 1.0) -> dict[str, float]:
    """Las operaciones que repiten los esqueletos, medidas en C++."""
    m = model_of(inst)
    if slot == "neighborhood":
        return {"delta": native.bench(m, "neighborhood", name, {}, sols, seconds),
                "ts_step": native.bench(m, "neighborhood_ts", name, {}, sols, seconds),
                "walk": native.bench(m, "neighborhood_walk", name, {}, sols, seconds)}
    return {slot: native.bench(m, slot, name, {}, sols, seconds)}


def optimize_check(request: dict) -> None:
    """La versión optimizada de un componente aceptado: pasa las capas, da las mismas salidas que la aceptada y es al
    menos `min_speedup` veces más rápida en alguna medida (en la trayectoria, el 40 % de esa mejora; medido en C++)."""
    from random import Random

    from core.validation.equivalence import check_component_equivalent
    from llm.cycle import base_pack, parts_contexts
    from llm.generator import validate_factory
    from native.generated import ModelCache, factory, load, parts_for

    pack = base_pack(request["problem"])
    gen = importlib.import_module(pack.native_module).GENERATION
    mip = importlib.import_module(gen["mip_parts"])
    old, new = load(request["old_so"], request["old_module"]), load(request["so"], request["module"])
    old_of, parts = ModelCache(old), parts_for(new, mip)
    name, slot = request["candidate"], request["component"]["slot"]
    comp = dict(request["component"])
    comp["compatible_skeletons"] = NATIVE_SKELETONS_FOR_SLOT[slot]
    contexts = parts_contexts(pack, parts, strict=False, reference_free=True)
    report = validate_factory(comp, factory(new, parts.model, slot, name), contexts)
    out = {"passed": report.passed, "failed_layer": report.failed_layer, "feedback": report.feedback()}
    inst, sols = bench_solutions(pack)
    if report.passed:
        if slot in ("neighborhood", "perturbation"):
            P = pack.problem_factory(inst)
            eq = check_component_equivalent(slot, factory(old, old_of, slot, name)(P), factory(new, parts.model, slot, name)(P),
                                            P, [mip.trivial_solution(inst)] + sols)
        else:  # mismos puntajes = mismas construcciones con cualquier regla y semilla
            from core.validation.base import ValidationReport, fail, ok

            eq = ValidationReport(subject=f"equivalencia ({slot})")
            cname = f"greedy_{name}" if slot == "greedy_score" else name
            for rule in ("greedy", "rcl", "roulette"):
                for seed in range(3):
                    a = old.make_constructor(old_of(inst), cname, {"rule": rule, "alpha": 0.3}).build(seed)
                    b = new.make_constructor(parts.model(inst), cname, {"rule": rule, "alpha": 0.3}).build(seed)
                    if a != b:
                        eq.add(fail("equivalence", "same_constructions", f"con la regla {rule} y la semilla {seed} el "
                                                                         f"constructor arma otra solución: los puntajes cambiaron"))
                        break
            if eq.passed:
                eq.add(ok("equivalence", "same_constructions"))
        out.update(passed=eq.passed, failed_layer=eq.failed_layer, feedback=eq.feedback())
    k = request.get("min_speedup", 1.5)
    before = speeds(old, old_of, slot, name, inst, sols)
    after = speeds(new, parts.model, slot, name, inst, sols) if out["passed"] else {m: 0.0 for m in before}
    out.update(before=before, after=after)
    if out["passed"]:
        ratios = {m: after[m] / max(before[m], 1e-9) for m in before}
        need = thresholds(before, k)
        if not any(ratios[m] >= need[m] for m in before) or min(ratios.values()) < 0.9:
            detail = "; ".join(f"{METRICS[m]}: {before[m]:,.0f} → {after[m]:,.0f} ({ratios[m]:.2f}×, se pide "
                               f"{need[m]:g}×)" for m in before)
            prof = profile(new, parts.model, slot, name, inst, sols)
            out.update(passed=False, failed_layer="speed",
                       feedback=f"mismas salidas, pero no alcanza: {detail}. Se pide que alguna medida mejore lo indicado y "
                                "que ninguna empeore más de un 10 %."
                                + (f"\nPerfil de tu versión: {prof}." if prof else ""))
    print(json.dumps(out))


if __name__ == "__main__":
    main(sys.argv[1])
