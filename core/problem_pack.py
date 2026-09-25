"""Lo que el framework recibe de un problema (`ProblemPack`).

El framework trae los esqueletos, el validador, el generador con LLM y el tuner. De cada
problema necesita solo esto:

- `problem_factory(inst)`: el `ProblemModel` ligado a una instancia (con `build_mip`,
  `variable_groups` y, si hay constructor modular, `construction_view`);
- `handwritten`: el catálogo de referencia, pares `(COMPONENT, fábrica)`; puede ser mínimo
  (una partida trivial y una política de fijación) si se genera desde cero;
- `make_spec()`: la descripción para el LLM (`llm.prompts.ProblemSpec`);
- `make_contexts(...)`: los micro-contextos de validación;
- `make_instances(n, seed0, size)` y `parse_size(texto)`: el generador de instancias;
- `baseline_constructor()`: la partida trivial, que normaliza el objetivo del tuner
  (costo / costo de la partida) para que ninguna instancia domine por escala;
- `load_instance(path)`: para irace.

`examples/lotsizing/pack.py` y `examples/cvrp/pack.py` son los dos que hay. Los módulos
genéricos (`llm.catalog`, `llm.cli`, `tuning.cli`) reciben un `ProblemPack` y no conocen
el problema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ProblemPack:
    name: str  # corto, para directorios y ramas: "clsp", "cvrp"
    module: str  # paquete Python del problema: "examples.lotsizing"
    problem_factory: Callable[[Any], Any]
    handwritten: list[tuple[dict, Callable]]
    make_spec: Callable[[], Any]
    make_contexts: Callable[..., list]
    make_instances: Callable[[int, int, dict], list]  # (n, seed0, size) -> instancias
    parse_size: Callable[[str], dict]
    default_size: str
    baseline_constructor: Callable[[], Any]
    load_instance: Callable[[str], Any]
    # esqueletos que puede usar un constructor (los greedy_<puntaje> se registran con estos)
    constructor_skeletons: list[str] = field(
        default_factory=lambda: ["SA", "ILS", "LNS_MIP", "FIX_OPT", "TS", "VNS", "GRASP", "LOCAL_BRANCH"])

    @property
    def default_workspace(self) -> str:
        return f"generated/{self.name}"

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
