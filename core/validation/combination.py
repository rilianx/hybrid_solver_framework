"""Validación por combinación: el componente dentro de cada esqueleto que declara.

Las capas anteriores juzgan el componente aislado. Las runs de tuning 2, 4 y 6 mostraron
que eso no alcanza: `drop_single_setup` y `left_shift_setup_chain` declaraban SA, ILS y
VNS, funcionaban en ILS y eran inertes en SA partiendo de lot-for-lot, pero no partiendo
del constructor greedy; `merge_with_previous_setup` era inerte desde lot-for-lot y parte de
la mejor configuración desde el greedy. La utilidad depende del esqueleto y de la partida.

Por eso, para cada esqueleto declarado (ver `SLOT_SKELETONS`; ILS se mide distinto, ver
ahí), se corre una variante corta desde
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

import functools
import time
from dataclasses import dataclass, field
from random import Random
from typing import Any, Callable

from .base import CheckResult, fail, ok

LAYER = "quality"

# Esqueletos donde se mide el aporte de cada slot. En SA, VNS, TS y GRASP el vecindario es
# el único motor de la búsqueda y se compara contra el vecindario nulo en el mismo tiempo.
# En ILS esa resta mezcla velocidad con aporte: con el nulo, ILS no gasta tiempo en búsqueda
# local y hace muchas más perturbaciones, y en 1 s casi todo vecindario real salía negativo
# (−7 % `setup_flip`, que en el tuning de 5 s es de lo mejor en ILS). Por eso en ILS el
# vecindario se juzga por lo que hace ahí, la búsqueda local: cuánto mejora `hill_climb`
# con muestreo a la partida y a perturbaciones de ella (`_ls_gain`; el nulo mejora 0).
# La perturbación se juzga por capacidad, no por mejora (`_pert_gain`): desde un óptimo local
# de la partida, ¿alguna patada seguida de búsqueda local termina en otra solución factible?
# Medir la mejora de un ILS corto no discrimina: con 1, 3 y 10 s salía ~0 para todas,
# incluida `item_break_repair`, que el tuner eligió en la run 6.
SLOT_SKELETONS = {
    "neighborhood": ["SA", "ILS", "VNS", "TS", "GRASP"],
    "perturbation": ["ILS"],
}

# Búsqueda local de la medición del vecindario en ILS: primera mejora sobre muestras de este
# tamaño, igual que el default de `ls_sample` en el ensamblador.
LS_SAMPLE = 32


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
    ils_budget: float = 4.0  # segundos por partida para las patadas de una perturbación en ILS
    kicks: int = 4
    converge_seconds: float = 30.0  # búsqueda local hasta el óptimo local de partida (perturbaciones)
    _null_gains: dict = field(default_factory=dict)  # (slot, esqueleto, partida) -> mejora del nulo
    _local_optima: dict = field(default_factory=dict)  # partida -> óptimo local (perturbaciones en ILS)


def _gain(assembler, P, instance, sk, slot, name, start, start_cost, budget, params=None) -> float:
    cfg = assembler.default_config(sk, {slot: name, "constructor": start})
    if params:
        cfg.update({f"{name}.{k}": v for k, v in params.items()})
    cost = assembler.evaluate(cfg, [instance], budget)
    return (start_cost - cost) / abs(start_cost) if start_cost else 0.0


def _ls_gain(assembler, P, instance, slot, name, start, start_sol, start_cost, budget, params=None) -> float:
    """Vecindario en ILS: mejora media que logra la búsqueda local con él sobre la partida y
    sobre dos perturbaciones factibles de ella (con la perturbación socia del registro),
    relativa al costo de la partida. El vecindario nulo mejora exactamente 0."""
    from skeletons.ils import hill_climb

    spec = assembler.registry.get(slot, name)
    kw = dict(spec.default_params())
    kw.update(params or {})
    nbh = spec.make(P, **kw)
    sols = [start_sol]
    perts = assembler.registry.compatible("perturbation", "ILS")
    if perts:
        pert = perts[0].make(P, **perts[0].default_params())
        # solo perturbaciones factibles: reparar una infactible (costo de penalización) no es
        # la mejora que interesa y dominaría el promedio
        sols += [x for x in (pert.perturb(start_sol, 2, Random(j)) for j in range(2)) if P.is_feasible(x)]
    ls = hill_climb(P, nbh, strategy="first", max_seconds=budget / len(sols), sample_size=LS_SAMPLE)
    total = 0.0
    for j, s0 in enumerate(sols):
        total += P.objective(s0) - P.objective(ls(s0, Random(j)))
    return total / len(sols) / abs(start_cost) if start_cost else 0.0


class _Fixed:
    """Constructor que devuelve siempre la misma solución (el óptimo local de partida)."""

    def __init__(self, sol):
        self.sol = sol

    def build(self, inst, rng):
        return self.sol


def _local_optimum(assembler, P, probe, start, start_sol):
    """Óptimo local de la partida con el vecindario socio de ILS: primera mejora con muestras
    hasta que una no mejora y después con recorrido completo, en total hasta
    `probe.converge_seconds` (en la sonda 10×15 del CLSP converge en ~13 s). Se calcula una
    vez por partida y se comparte entre todos los componentes que valida la sonda."""
    from skeletons.ils import hill_climb

    if start not in probe._local_optima:
        nbhs = assembler.registry.compatible("neighborhood", "ILS")
        if not nbhs:
            probe._local_optima[start] = start_sol
        else:
            nbh = nbhs[0].make(P, **nbhs[0].default_params())
            t0 = time.monotonic()
            sol = hill_climb(P, nbh, strategy="first", max_seconds=probe.converge_seconds,
                             sample_size=LS_SAMPLE)(start_sol, Random(0))
            left = max(0.0, probe.converge_seconds - (time.monotonic() - t0))
            probe._local_optima[start] = hill_climb(P, nbh, strategy="first", max_seconds=left)(sol, Random(0))
    return probe._local_optima[start]


def _pert_gain(assembler, P, instance, slot, name, start, start_sol, start_cost, budget, params=None, probe=None) -> float:
    """Perturbación en ILS: fracción de patadas desde un óptimo local de la partida que, tras
    la búsqueda local con el vecindario socio, terminan en OTRA solución factible (no la
    deshace la búsqueda local ni deja una infactible). Es un criterio de capacidad, no de
    calidad: con un `delta` que cuesta un LP, la mejora de un ILS en segundos es ruido
    (medida con 3 y 10 s salían en 0 perturbaciones que el tuner elige en la run 6)."""
    from skeletons.ils import hill_climb

    spec = assembler.registry.get(slot, name)
    kw = dict(spec.default_params())
    kw.update(params or {})
    pert = spec.make(P, **kw)
    nbhs = assembler.registry.compatible("neighborhood", "ILS")
    if not nbhs:
        return 0.0
    nbh = nbhs[0].make(P, **nbhs[0].default_params())
    s_star = _local_optimum(assembler, P, probe, start, start_sol)
    ls = hill_climb(P, nbh, strategy="first", max_seconds=probe.ils_budget / probe.kicks, sample_size=LS_SAMPLE)
    escaped = 0
    for j in range(probe.kicks):
        s = ls(pert.perturb(s_star, 1, Random(j)), Random(j))
        escaped += s != s_star and P.is_feasible(s)
    return escaped / probe.kicks


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
    start_cost, start_sol = {}, {}
    for st in probe.starts:
        spec = assembler.registry.get("constructor", st)
        start_sol[st] = spec.make(P, **spec.default_params()).build(probe.instance, Random(0))
        start_cost[st] = P.objective(start_sol[st])
    # En ILS (ver SLOT_SKELETONS) el vecindario se mide por su búsqueda local (el nulo mejora 0)
    # y la perturbación por si saca del óptimo local, restando la tasa de las patadas nulas.
    direct = lambda sk: sk == "ILS"  # noqa: E731
    direct_measure = {"neighborhood": _ls_gain, "perturbation": functools.partial(_pert_gain, probe=probe)}
    gains: dict[str, float] = {}
    useful: list[str] = []
    available = set(assembler.available_skeletons())
    tested = [sk for sk in cands if sk in available]
    for sk in tested:
        for st in probe.starts:
            key = (slot, sk, st)
            if direct(sk) and slot == "neighborhood":
                probe._null_gains[key] = 0.0
            elif direct(sk) and key not in probe._null_gains:
                # patadas nulas: ≈ 0 si la búsqueda local convergió; si no, lo que la búsqueda
                # local siga bajando desde el "óptimo" no se le abona a la perturbación
                probe._null_gains[key] = direct_measure[slot](null_assembler, P, probe.instance, slot, null_name, st,
                                                              start_sol[st], start_cost[st], probe.budget)
            elif key not in probe._null_gains:
                probe._null_gains[key] = _gain(null_assembler, P, probe.instance, sk, slot, null_name, st, start_cost[st], probe.budget)
    param_space = dict(component.get("params") or {})
    trials = [None] + [_sample_params(param_space, Random(k)) for k in range(probe.param_samples if param_space else 0)]
    tried_params = None
    for params in trials:
        for sk in tested:
            for st in probe.starts:
                measure = direct_measure[slot] if direct(sk) else _gain
                args = (slot, name, st, start_sol[st]) if direct(sk) else (sk, slot, name, st)
                marginal = measure(assembler, P, probe.instance, *args, start_cost[st], probe.budget, params) \
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
        if slot == "perturbation":
            why = (f"desde un óptimo local de cada constructor de partida ({', '.join(probe.starts)}), ninguna de "
                   f"{probe.kicks} patadas seguidas de búsqueda local terminó en otra solución factible "
                   f"(con los parámetros por defecto y {len(trials) - 1} configuraciones al azar): {detail}. La búsqueda "
                   f"local deshace la perturbación o la deja infactible; el ILS nunca sale del óptimo local. Revisa que la "
                   f"perturbación cambie la solución lo suficiente y mantenga la factibilidad.")
        else:
            why = (f"corrido {probe.budget:.1f} s en cada esqueleto que declaras ({', '.join(tested)}) desde cada "
                   f"constructor de partida ({', '.join(probe.starts)}), con los parámetros por defecto y "
                   f"{len(trials) - 1} configuraciones al azar, no aporta al menos {probe.min_gain:.1%} sobre "
                   f"el mismo esqueleto con un componente nulo en ninguno (en ILS: lo que mejora su búsqueda local): "
                   f"{detail}. Es un operador correcto pero inerte dentro de los algoritmos reales; revisa que sus "
                   f"movimientos puedan mejorar soluciones como las de partida.")
        return [fail(LAYER, f"{slot}.useful_in_some_skeleton", why)], keep, gains
    msg = f"aporta en {', '.join(useful)}" + (f"; se quita de {', '.join(dropped)} (sin aporte desde ninguna partida)" if dropped else "")
    if tried_params:
        msg += f" (con parámetros {tried_params}; con los por defecto no aportaba)"
    label = "patadas que salen del óptimo local" if slot == "perturbation" else "aporte sobre el nulo"
    return [ok(LAYER, f"{slot}.useful_in_some_skeleton", f"{msg} · {label}: {detail}")], keep, gains


__all__ = ["CombinationProbe", "IdentityNeighborhood", "IdentityPerturbation", "SLOT_SKELETONS", "check_combinations"]
