"""Validación por combinación: el componente dentro de cada esqueleto que declara.

Las capas anteriores juzgan el componente aislado. Las runs de tuning 2, 4 y 6 mostraron
que eso no alcanza: `drop_single_setup` y `left_shift_setup_chain` declaraban SA, ILS y
VNS, funcionaban en ILS y eran inertes en SA partiendo de lot-for-lot, pero no partiendo
del constructor greedy; `merge_with_previous_setup` era inerte desde lot-for-lot y parte de
la mejor configuración desde el greedy. La utilidad depende del esqueleto y de la partida.

Por eso, para cada esqueleto declarado donde el componente es el único motor de la
búsqueda (ver `SLOT_SKELETONS`), se corre una variante corta desde
CADA constructor de partida de la sonda y se mide su aporte MARGINAL: la mejora sobre la
partida menos la que logra el mismo esqueleto con un componente nulo (un vecindario cuyo
único movimiento deja la solución igual). En VNS, además, los demás vecindarios
registrados (que usa para el shake) harían el trabajo: en la sonda no se registran los de
mano del mismo slot, y el nulo se mide en un registro donde es el único.

Con los parámetros por defecto un componente puede ser inerte y útil con otros
(`merge_with_previous_setup`, corrida 10: `min_savings_margin = 500` filtraba casi todo, y
con los parámetros que eligió el tuner fue parte de la mejor configuración de la run 6).
Por eso, si no aporta con los defaults, se prueban `param_samples` configuraciones al azar
dentro de los rangos declarados antes de concluir. Un esqueleto se conserva si el aporte es
al menos `min_gain` desde alguna partida; los demás se quitan de `compatible_skeletons` y,
si no queda ninguno, el componente se rechaza.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from random import Random
from typing import Any, Callable

from .base import CheckResult, fail, ok

LAYER = "quality"

# Esqueletos donde el componente es el ÚNICO motor de la búsqueda, y por eso su aporte se
# puede aislar con una corrida corta. ILS queda fuera a propósito: con el vecindario nulo,
# ILS no gasta tiempo en búsqueda local y hace muchas más perturbaciones, así que en 1 s
# todo vecindario real sale negativo (−10 %, incluido `merge_consecutive_setups`, que en el
# tuning de 5 s rinde como `setup_flip` en ILS): la resta mezcla velocidad con aporte. Por la
# misma razón no se juzgan las perturbaciones (su único esqueleto es ILS): con 1 s, una
# instancia y una semilla, el orden salió al revés que en el tuning de la run 2.
SLOT_SKELETONS = {
    "neighborhood": ["SA", "VNS", "TS", "GRASP"],
}


class IdentityNeighborhood:
    """Vecindario nulo: un único movimiento que deja la solución igual."""

    def moves(self, sol):
        return [None]

    def apply(self, sol, m):
        return sol

    def undo(self, sol, m):
        return sol

    def delta(self, sol, m):
        return 0.0


class IdentityPerturbation:
    """Perturbación nula: no cambia nada (ILS queda reducido a su búsqueda local)."""

    def perturb(self, sol, strength, rng):
        return sol


NULL_IMPL = {"neighborhood": IdentityNeighborhood, "perturbation": IdentityPerturbation}


@dataclass
class CombinationProbe:
    instance: Any
    # (slot, [(COMPONENT, fábrica), ...]) -> Assembler con socios de mano para los DEMÁS slots,
    # los constructores de partida y estos componentes registrados (sin los de mano del slot).
    assembler_for: Callable[[str, list], Any]
    starts: list[str] = field(default_factory=list)  # nombres de constructores de partida
    budget: float = 1.0
    min_gain: float = 0.005
    param_samples: int = 3
    _null_gains: dict = field(default_factory=dict)  # (slot, esqueleto, partida) -> mejora del nulo


def _gain(assembler, P, instance, sk, slot, name, start, start_cost, budget, params=None) -> float:
    cfg = assembler.default_config(sk, {slot: name, "constructor": start})
    if params:
        cfg.update({f"{name}.{k}": v for k, v in params.items()})
    cost = assembler.evaluate(cfg, [instance], budget)
    return (start_cost - cost) / abs(start_cost) if start_cost else 0.0


def _sample_params(spec_params: dict, rng: Random) -> dict:
    out = {}
    for pname, ps in spec_params.items():
        t = ps.get("type")
        if t == "int":
            lo, hi = ps["range"]
            out[pname] = rng.randint(int(lo), int(hi))
        elif t == "float":
            lo, hi = ps["range"]
            out[pname] = rng.uniform(float(lo), float(hi))
        elif t == "cat":
            out[pname] = rng.choice(list(ps["values"]))
        elif t == "bool":
            out[pname] = rng.random() < 0.5
    return out


def check_combinations(component: dict, factory, probe: CombinationProbe) -> tuple[list[CheckResult], list[str], dict[str, float]]:
    """(resultados, compatible_skeletons a conservar, aporte marginal por esqueleto/partida)."""
    slot, name = component.get("slot"), component.get("name")
    declared = list(component.get("compatible_skeletons") or [])
    cands = [sk for sk in SLOT_SKELETONS.get(slot, []) if sk in declared]
    if not cands or not probe.starts or slot not in NULL_IMPL:
        return [], declared, {}
    null_name = f"_null_{slot}"
    null_dict = {"name": null_name, "slot": slot, "compatible_skeletons": SLOT_SKELETONS[slot], "params": {}}
    null_factory = lambda problem: NULL_IMPL[slot]()  # noqa: E731
    assembler = probe.assembler_for(slot, [(component, factory)])
    null_assembler = probe.assembler_for(slot, [(null_dict, null_factory)])  # el nulo solo: sin el componente en el shake
    name = getattr(assembler, "probe_component", name)
    P = assembler.problem_factory(probe.instance)
    start_cost = {}
    for st in probe.starts:
        spec = assembler.registry.get("constructor", st)
        start_cost[st] = P.objective(spec.make(P, **spec.default_params()).build(probe.instance, Random(0)))
    gains: dict[str, float] = {}
    useful: list[str] = []
    available = set(assembler.available_skeletons())
    tested = [sk for sk in cands if sk in available]
    for sk in tested:
        for st in probe.starts:
            key = (slot, sk, st)
            if key not in probe._null_gains:
                probe._null_gains[key] = _gain(null_assembler, P, probe.instance, sk, slot, null_name, st, start_cost[st], probe.budget)
    param_space = dict(component.get("params") or {})
    trials = [None] + [_sample_params(param_space, Random(k)) for k in range(probe.param_samples if param_space else 0)]
    tried_params = None
    for params in trials:
        for sk in tested:
            for st in probe.starts:
                marginal = _gain(assembler, P, probe.instance, sk, slot, name, st, start_cost[st], probe.budget, params) \
                    - probe._null_gains[(slot, sk, st)]
                k = f"{sk}/{st}"
                gains[k] = round(max(marginal, gains.get(k, marginal)), 4)
                if marginal >= probe.min_gain and sk not in useful:
                    useful.append(sk)
        if useful:
            tried_params = params
            break
    keep = [sk for sk in declared if sk not in tested or sk in useful]
    dropped = [sk for sk in tested if sk not in useful]
    detail = ", ".join(f"{k} {v:+.1%}" for k, v in gains.items())
    if tested and not useful:
        return [fail(LAYER, f"{slot}.useful_in_some_skeleton",
                     f"corrido {probe.budget:.1f} s en cada esqueleto que declaras ({', '.join(tested)}) desde cada "
                     f"constructor de partida ({', '.join(probe.starts)}), con los parámetros por defecto y "
                     f"{len(trials) - 1} configuraciones al azar, no aporta al menos {probe.min_gain:.1%} sobre "
                     f"el mismo esqueleto con un componente nulo en ninguno: {detail}. Es un operador correcto pero inerte "
                     f"dentro de los algoritmos reales; revisa que sus movimientos puedan mejorar soluciones como las de partida.")], keep, gains
    msg = f"aporta en {', '.join(useful)}" + (f"; se quita de {', '.join(dropped)} (sin aporte desde ninguna partida)" if dropped else "")
    if tried_params:
        msg += f" (con parámetros {tried_params}; con los por defecto no aportaba)"
    return [ok(LAYER, f"{slot}.useful_in_some_skeleton", f"{msg} · aporte sobre el nulo: {detail}")], keep, gains


__all__ = ["CombinationProbe", "IdentityNeighborhood", "IdentityPerturbation", "SLOT_SKELETONS", "check_combinations"]
