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
    from llm.cycle import base_pack, parts_contexts
    from llm.generator import validate_factory
    from native.generated import factory, load, parts_for

    request = json.loads(Path(path).read_text())
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


if __name__ == "__main__":
    main(sys.argv[1])
