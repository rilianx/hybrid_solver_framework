"""Ensamblador (§2, §8): configuración → variante ejecutable → costo.

    config = {"skeleton": "LNS_MIP", "constructor": "lot_for_lot", "destruction": "period_window",
              "period_window.ratio": 0.3, "LNS_MIP.mip_time_limit": 2.0, ...}
    runner = assembler.assemble(config)          # (inst, rng, budget) -> RunResult
    cost   = assembler.evaluate(config, instances, budget, seed)   # lo que llama el tuner

El `Assembler` conoce qué slots usa cada esqueleto y los parámetros propios
de cada uno (`SKELETONS`); con eso construye el `ConfigSpace` (§8) y, dado
un punto de ese espacio, instancia cada componente vía `ComponentSpec.make`
y arma el `TrajectorySkeleton` correspondiente con `MaxTimeStop(budget)`.
Nada aquí conoce el problema: todo pasa por el registro y el ProblemModel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from statistics import mean
from typing import Any, Callable

from config_space.space import ConfigSpace, build_config_space
from core.common_components import BetterAcceptance, MIPModelRepair, MaxTimeStop
from core.component import ComponentRegistry, ComponentSpec
from core.skeleton import RunResult
from skeletons.fix_and_optimize import build_fix_and_optimize, run_fix_and_optimize
from skeletons.grasp import build_grasp, run_grasp
from skeletons.ils import build_ils, hill_climb
from skeletons.lns_mip import build_lns_mip, run_lns_mip
from skeletons.local_branching import build_local_branching, run_local_branching
from skeletons.sa import MetropolisAcceptance, build_sa, make_run
from skeletons.ts import build_ts
from skeletons.vns import build_vns

VariantRunner = Callable[[Any, Random, float], RunResult]


@dataclass(frozen=True)
class SkeletonDef:
    name: str
    slots: tuple[str, ...]  # slots obligatorios que se leen de la configuración
    optional_slots: tuple[str, ...] = ()  # se usan si el registro los tiene; si no, default del núcleo
    params: dict[str, dict[str, Any]] = field(default_factory=dict)


SKELETONS: dict[str, SkeletonDef] = {
    "SA": SkeletonDef(
        "SA", ("constructor", "neighborhood"),
        params={
            "T0": {"type": "float", "range": [1.0, 1000.0], "log": True},
            "alpha": {"type": "float", "range": [0.8, 0.999]},
            "iters_per_T": {"type": "int", "range": [1, 50]},
        },
    ),
    "ILS": SkeletonDef(
        "ILS", ("constructor", "neighborhood", "perturbation"),
        params={
            "strength": {"type": "int", "range": [1, 6]},
            "ls_strategy": {"type": "cat", "values": ["first", "best"]},
            "ls_time_share": {"type": "float", "range": [0.02, 0.3]},
        },
    ),
    "LNS_MIP": SkeletonDef(
        "LNS_MIP", ("constructor", "destruction"), optional_slots=("repair_mip",),
        params={
            "destroy_ratio": {"type": "float", "range": [0.05, 0.6]},
            "mip_time_share": {"type": "float", "range": [0.02, 0.3], "log": True},
        },
    ),
    "FIX_OPT": SkeletonDef(
        "FIX_OPT", ("constructor", "fixing_policy"),
        params={
            "block_size": {"type": "int", "range": [1, 4]},
            "mip_time_share": {"type": "float", "range": [0.02, 0.3], "log": True},
            "order": {"type": "cat", "values": ["sequential", "random"]},
        },
    ),
    "TS": SkeletonDef(
        "TS", ("constructor", "neighborhood"),
        params={
            "tenure": {"type": "int", "range": [3, 30]},
            "candidate_size": {"type": "int", "range": [5, 100], "log": True},
        },
    ),
    "VNS": SkeletonDef(
        # `neighborhood` es el de la búsqueda local; para el shake se usan, en orden,
        # todos los vecindarios compatibles del catálogo (k_max = cuántos hay).
        "VNS", ("constructor", "neighborhood"),
        params={
            "shake_strength": {"type": "int", "range": [1, 4]},
            "ls_time_share": {"type": "float", "range": [0.02, 0.3]},
        },
    ),
    "GRASP": SkeletonDef(
        "GRASP", ("constructor", "neighborhood"),
        params={
            "ls_strategy": {"type": "cat", "values": ["first", "best"]},
            "ls_time_share": {"type": "float", "range": [0.02, 0.3]},
        },
    ),
    "LOCAL_BRANCH": SkeletonDef(
        "LOCAL_BRANCH", ("constructor",),
        params={
            "k": {"type": "int", "range": [2, 20]},
            "k_step": {"type": "int", "range": [1, 10]},
            "mip_time_share": {"type": "float", "range": [0.05, 0.5], "log": True},
        },
    ),
}


class AssemblyError(ValueError):
    pass


@dataclass
class Assembler:
    problem_factory: Callable[[Any], Any]  # inst -> ProblemModel ligado a esa instancia
    registry: ComponentRegistry
    skeletons: dict[str, SkeletonDef] = field(default_factory=lambda: dict(SKELETONS))
    penalty_cost: float = 1e12  # costo devuelto cuando una variante falla (§8: "penalized si falla")

    # ------------------------------------------------------------------ espacio
    def available_skeletons(self) -> list[str]:
        """Esqueletos para los que el registro tiene al menos un componente por slot obligatorio."""
        out = []
        for name, sk in self.skeletons.items():
            if all(self.registry.compatible(slot, name) for slot in sk.slots):
                out.append(name)
        return out

    def config_space(self) -> ConfigSpace:
        names = self.available_skeletons()
        if not names:
            raise AssemblyError("ningún esqueleto tiene componentes registrados para todos sus slots")
        return build_config_space(
            self.registry,
            skeleton_names=names,
            slots_per_skeleton={n: list(self.skeletons[n].slots) + [s for s in self.skeletons[n].optional_slots if self.registry.compatible(s, n)] for n in names},
            skeleton_params={n: self.skeletons[n].params for n in names},
        )

    def default_config(self, skeleton: str, choices: dict[str, str] | None = None) -> dict[str, Any]:
        """Configuración completa con defaults: útil para smoke tests y como punto inicial del tuner."""
        sk = self.skeletons[skeleton]
        config: dict[str, Any] = {"skeleton": skeleton}
        for slot in sk.slots + tuple(s for s in sk.optional_slots if self.registry.compatible(s, skeleton)):
            options = self.registry.compatible(slot, skeleton)
            spec = self.registry.get(slot, choices[slot]) if choices and slot in choices else options[0]
            config[slot] = spec.name
            for p, v in spec.default_params().items():
                config[f"{spec.name}.{p}"] = v
        for p, pspec in sk.params.items():
            config[f"{skeleton}.{p}"] = ComponentSpec("_", "stop", (), (), {p: pspec}, None).default_params()[p]
        return config

    # ------------------------------------------------------------------ ensamblaje
    def _component(self, config: dict[str, Any], slot: str, skeleton: str, problem: Any, required: bool = True):
        name = config.get(slot)
        if name is None:
            if required:
                raise AssemblyError(f"la configuración no elige componente para el slot '{slot}' (esqueleto {skeleton})")
            return None
        spec = self.registry.get(slot, name)
        if not spec.is_compatible_with(skeleton):
            raise AssemblyError(f"'{name}' ({slot}) no es compatible con el esqueleto {skeleton}")
        params = {p: config[f"{name}.{p}"] for p in spec.params if f"{name}.{p}" in config}
        return spec.make(problem, **params)

    def _skeleton_param(self, config: dict[str, Any], skeleton: str, p: str):
        key = f"{skeleton}.{p}"
        if key in config:
            return config[key]
        pspec = self.skeletons[skeleton].params[p]
        return ComponentSpec("_", "stop", (), (), {p: pspec}, None).default_params()[p]

    def assemble(self, config: dict[str, Any]) -> VariantRunner:
        """Devuelve `run(inst, rng, budget)`. Los componentes se instancian al correr,
        ligados al ProblemModel de esa instancia (`problem_factory(inst)`)."""
        skeleton = config.get("skeleton")
        if skeleton not in self.skeletons:
            raise AssemblyError(f"esqueleto desconocido: {skeleton!r}")
        sp = lambda p: self._skeleton_param(config, skeleton, p)  # noqa: E731
        # validación temprana de la configuración (sin instancia): nombres y compatibilidad
        for slot in self.skeletons[skeleton].slots:
            name = config.get(slot)
            if name is None:
                raise AssemblyError(f"la configuración no elige componente para el slot '{slot}' (esqueleto {skeleton})")
            try:
                spec = self.registry.get(slot, name)
            except KeyError as exc:
                raise AssemblyError(str(exc)) from exc
            if not spec.is_compatible_with(skeleton):
                raise AssemblyError(f"'{name}' ({slot}) no es compatible con el esqueleto {skeleton}")

        def run(inst, rng: Random, budget: float) -> RunResult:
            P = self.problem_factory(inst)
            constructor = self._component(config, "constructor", skeleton, P)
            if skeleton == "SA":
                nbh = self._component(config, "neighborhood", skeleton, P)
                sk, extra = build_sa(P, constructor, nbh, MaxTimeStop(budget), T0=sp("T0"), alpha=sp("alpha"),
                                     iters_per_T=sp("iters_per_T"), acceptance=MetropolisAcceptance())
                return make_run(sk, extra)(inst, rng)
            if skeleton == "ILS":
                nbh = self._component(config, "neighborhood", skeleton, P)
                pert = self._component(config, "perturbation", skeleton, P)
                ls = hill_climb(P, nbh, strategy=sp("ls_strategy"), max_seconds=budget * sp("ls_time_share"))
                sk = build_ils(P, constructor, ls, pert, BetterAcceptance(), MaxTimeStop(budget), strength=sp("strength"))
                return sk.run(inst, rng)
            if skeleton == "LNS_MIP":
                destr = self._component(config, "destruction", skeleton, P)
                repair = self._component(config, "repair_mip", skeleton, P, required=False) or MIPModelRepair(P)
                ratio = sp("destroy_ratio")
                sk = build_lns_mip(P, constructor, destr, repair, BetterAcceptance(), MaxTimeStop(budget),
                                   destroy_ratio=ratio, mip_time_limit=max(1.0, budget * sp("mip_time_share")))
                return run_lns_mip(sk, inst, rng, ratio)
            if skeleton == "FIX_OPT":
                policy = self._component(config, "fixing_policy", skeleton, P)
                sk = build_fix_and_optimize(P, constructor, policy, BetterAcceptance(), MaxTimeStop(budget),
                                            block_size=sp("block_size"), time_limit=max(1.0, budget * sp("mip_time_share")),
                                            order=sp("order"))
                return run_fix_and_optimize(sk, inst, rng)
            if skeleton == "TS":
                nbh = self._component(config, "neighborhood", skeleton, P)
                sk = build_ts(P, constructor, nbh, MaxTimeStop(budget), tenure=sp("tenure"), candidate_size=sp("candidate_size"))
                return sk.run(inst, rng)
            if skeleton == "VNS":
                ls_nbh = self._component(config, "neighborhood", skeleton, P)
                others = [
                    spec.make(P, **{p_: config[f"{spec.name}.{p_}"] for p_ in spec.params if f"{spec.name}.{p_}" in config})
                    for spec in self.registry.compatible("neighborhood", skeleton)
                    if spec.name != config["neighborhood"]
                ]
                sk = build_vns(P, constructor, [ls_nbh] + others, MaxTimeStop(budget),
                               shake_strength=sp("shake_strength"), ls_max_seconds=budget * sp("ls_time_share"))
                return sk.run(inst, rng)
            if skeleton == "GRASP":
                nbh = self._component(config, "neighborhood", skeleton, P)
                sk = build_grasp(P, constructor, nbh, MaxTimeStop(budget), ls_strategy=sp("ls_strategy"),
                                 ls_max_seconds=budget * sp("ls_time_share"))
                return run_grasp(sk, inst, rng)
            if skeleton == "LOCAL_BRANCH":
                sk = build_local_branching(P, constructor, MaxTimeStop(budget), k=sp("k"), k_step=sp("k_step"),
                                           time_limit=max(1.0, budget * sp("mip_time_share")))
                return run_local_branching(sk, inst, rng)
            raise AssemblyError(f"esqueleto {skeleton} declarado pero sin constructor de variante")

        return run

    # ------------------------------------------------------------------ target-runner
    def evaluate(self, config: dict[str, Any], instances: list[Any], budget: float, seed: int = 0,
                 on_error: str = "penalize") -> float:
        """Costo medio de la configuración sobre `instances` con `budget` s por corrida.

        Es el *target runner* de §8: recibe la configuración, ensambla y ejecuta.
        Si la variante falla o devuelve infactible, retorna `penalty_cost`
        (o relanza si `on_error="raise"`).
        """
        try:
            runner = self.assemble(config)
            costs = []
            for k, inst in enumerate(instances):
                result = runner(inst, Random(seed + k), budget)
                if not self.problem_factory(inst).is_feasible(result.best_solution):
                    return self.penalty_cost
                costs.append(result.best_objective)
            return mean(costs)
        except Exception:
            if on_error == "raise":
                raise
            return self.penalty_cost


def describe(config: dict[str, Any]) -> str:
    """Resumen legible de una configuración: esqueleto + componentes elegidos."""
    sk = config.get("skeleton", "?")
    slots = [f"{k}={v}" for k, v in config.items() if k in {"constructor", "neighborhood", "perturbation", "destruction", "repair_mip", "fixing_policy"}]
    return f"{sk}[{', '.join(slots)}]"
