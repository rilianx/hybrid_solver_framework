"""Lo que el framework recibe de un problema (`ProblemPack`).

El framework trae los esqueletos, el validador, el generador con LLM y el tuner. De cada
problema necesita solo esto:

- `problem_factory(inst)`: el `ProblemModel` ligado a una instancia (con `build_mip` y `variable_groups`);
- `base_components`: los componentes genéricos del framework para este problema, pares `(COMPONENT, fábrica)`
  (`core.packs.base_components`: las partidas trivial y al azar y, con vista MIP, las destrucciones de HYB); el
  resto del catálogo lo escribe el LLM;
- `make_contexts(...)`: los micro-contextos de validación (`core.packs.parts_contexts`);
- `make_instances(n, seed0, size)` y `parse_size(texto)`: el generador de instancias;
- `baseline_constructor()`: la partida trivial, que normaliza el objetivo del tuner
  (costo / costo de la partida) para que ninguna instancia domine por escala;
- `load_instance(path)`: para irace.

Los packs están en `examples/*/pack.py` (registro en `core.packs.PACKS`). Los módulos genéricos
(`core.catalog`, `native/check*.py`, `llm.native_*`, `tuning.cli`) reciben un `ProblemPack` y no
conocen el problema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ProblemPack:
    name: str  # corto, para directorios y ramas: "clsp", "cvrp"
    module: str  # paquete Python del problema: "examples.lotsizing"
    problem_factory: Callable[[Any], Any]
    make_instances: Callable[[int, int, dict], list]  # (n, seed0, size) -> instancias
    parse_size: Callable[[str], dict]
    default_size: str
    baseline_constructor: Callable[[], Any]
    load_instance: Callable[[str], Any]
    base_components: list[tuple[dict, Callable]] = field(default_factory=list)
    make_contexts: Callable[..., list] | None = None
    # generación del ProblemModel con LLM (§6.1): descripción para el LLM y tamaño de las micro-instancias
    make_model_spec: Callable[[], Any] | None = None
    micro_size: str = ""
    load_cases: Callable[[], list] | None = None  # casos de prueba al estilo Codeforces (core.model_parts.TestCase)
    # representaciones del problema: {nombre: (make_model_spec, piezas de referencia importables)}; la primera es la que
    # usa la generación nativa (`llm.native_model_generator`) como oráculo y vista MIP.
    variants: dict[str, tuple[Callable[[], Any], str]] = field(default_factory=dict)
    # backend nativo (C++), opcional: módulo con `native` (bindings) y `model(inst)` (ver `core.native_runner`)
    native_module: str = ""
    # factor del presupuesto por instancia (con `--scale-budget`): el tiempo crece con el tamaño, como en los protocolos
    # de la literatura (p.ej. n·m/2·t ms en el flow shop); 1 en el tamaño de referencia
    budget_scale: Callable[[Any], float] | None = None
    bench_size: str = ""  # tamaño de las instancias donde se mide la velocidad de los componentes (vacío = default_size)
    # esqueletos que puede usar un constructor (los greedy_<puntaje> se registran con estos)
    constructor_skeletons: list[str] = field(
        default_factory=lambda: ["SA", "ILS", "TS", "VNS", "PR", "HYB"])

    @property
    def default_workspace(self) -> str:
        return f"generated/{self.name}_native"

    def baseline_cost(self, inst) -> float:
        from random import Random

        return self.problem_factory(inst).objective(self.baseline_constructor().build(inst, Random(0)))

    def mip_reference(self, inst, seconds: float) -> float | None:
        """Costo de la mejor solución que el MIP completo encuentra en `seconds` (None si
        ninguna factible)."""
        P = self.problem_factory(inst)
        model = P.build_mip(inst)
        x = model.solve(fixed={}, integer=set(model.variables()), relaxed=set(), time_limit=seconds)
        if x is None:
            return None
        sol = P.from_assignment(x)
        return P.objective(sol) if P.is_feasible(sol) else None


__all__ = ["ProblemPack"]
