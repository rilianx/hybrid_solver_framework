"""Máquinas de reglas: reglas de acción + transiciones (lo que genera y evoluciona el LLM).

Una heurística constructiva como FRG no puntúa todos los candidatos: tiene REGLAS DE ACCIÓN que
proponen un movimiento concreto (o dicen "no aplico") y un CONTROLADOR que decide cuál usar.

    class Regla:                                   # p.ej. bg_move, reduce_stack
        name = "reduce_stack"
        propose(parcial, memoria) -> [acciones]    # en orden de preferencia; [] = no aplica
        init(parcial) -> memoria                   # opcional (default ())
        start(parcial, memoria) -> memoria         # opcional: al activarse (elegir la pila a reducir)
        update(parcial, memoria, acción) -> memoria  # opcional: tras hacer la acción
        done(parcial, memoria) -> bool             # opcional: ¿terminó su compromiso? (default True)

    class Transiciones:
        initial(parcial) -> memoria                # opcional (default ())
        select(parcial, memoria, reglas) -> (nombre de regla o FALLBACK, memoria)

`reglas` (`RuleView`) le dice al controlador `active` (la regla activa o None), `applies(n)` (si
la regla n propondría algo, activándola si no lo está) y `done(n)` (si la activa terminó su
compromiso). FRG:

    if reglas.active == "reduce_stack" and not reglas.done("reduce_stack"): sigue reduce_stack
    elif reglas.applies("bg_move"): bg_move
    else: reduce_stack                             # al (re)activarse elige otra pila

`RuleMachine(problem, reglas, transiciones)` es una `ConstructionMachine` (estados = nombres de las
reglas): el greedy, la beam search, la validación, los parámetros y el diagnóstico por estado de
`core.machine` la usan sin cambios. La lista de una regla se vuelve puntaje por su posición; lo
que no propone vale `FAR`. Si la regla elegida no propone nada, decide el comodín (`FALLBACK`).

Separar reglas y transiciones da operadores más finos a `llm.evolve` (agregar una regla, refinar
una regla sin tocar las demás, cambiar solo las transiciones) y un diagnóstico por regla con el
oráculo (`rule_quality`): cobertura (en cuántos pasos aplica) y precisión (cuando aplica, qué
fracción de las veces su primera propuesta es óptima).
"""

from __future__ import annotations

from typing import Any, Sequence

from .machine import FALLBACK

FAR = 1e6  # puntaje de lo que la regla activa no propone


def _call(obj, name, default, *args):
    fn = getattr(obj, name, None)
    return default if fn is None else fn(*args)


class RuleView:
    """Lo que ve el controlador en un paso: qué regla está activa, cuáles aplican, si la activa terminó."""

    def __init__(self, machine: "RuleMachine", partial: Any, mems: tuple, active: str | None):
        self._m, self._partial, self._mems, self.active = machine, partial, mems, active
        self.names = machine.states

    def _mem(self, name: str):
        i = self._m.index[name]
        mem = self._mems[i]
        if name != self.active:  # una regla inactiva se consulta como si se activara ahora
            mem = _call(self._m.rules[i], "start", mem, self._partial, mem)
        return mem

    def proposal(self, name: str) -> list:
        return self._m.propose(name, self._partial, self._mem(name))

    def applies(self, name: str) -> bool:
        return bool(self.proposal(name))

    def done(self, name: str) -> bool:
        i = self._m.index[name]
        return bool(_call(self._m.rules[i], "done", True, self._partial, self._mems[i]))


class RuleMachine:
    """Reglas de acción + transiciones como `ConstructionMachine`. Memoria: (la del controlador, la
    de cada regla)."""

    def __init__(self, problem: Any, rules: Sequence[Any], transitions: Any):
        self.problem = problem
        self.rules = list(rules)
        self.transitions = transitions
        names = [getattr(r, "name", None) for r in self.rules]
        if any(not isinstance(n, str) for n in names) or len(set(names)) != len(names):
            raise ValueError(f"cada regla necesita un `name` (str) distinto; hay {names}")
        self.states = tuple(names)
        self.index = {n: i for i, n in enumerate(names)}
        self._cache: tuple | None = None  # (parcial, regla, memoria, propuesta): score se llama por candidato

    def propose(self, name: str, partial: Any, mem: Any) -> list:
        c = self._cache
        if c is not None and c[0] is partial and c[1] == name and c[2] == mem:
            return c[3]
        out = list(self.rules[self.index[name]].propose(partial, mem) or [])
        self._cache = (partial, name, mem, out)
        return out

    def initial(self, partial):
        """Ninguna regla activa todavía: la primera transición (antes del primer paso) elige y la activa."""
        cmem = _call(self.transitions, "initial", (), partial)
        mems = tuple(_call(r, "init", (), partial) for r in self.rules)
        return FALLBACK, (cmem, mems)

    def transition(self, partial, state, memory):
        cmem, mems = memory
        active = state if state in self.index else None
        view = RuleView(self, partial, mems, active)
        out = self.transitions.select(partial, cmem, view)
        if not (isinstance(out, tuple) and len(out) == 2):
            raise TypeError(f"select debe devolver (nombre de regla o FALLBACK, memoria), no {out!r}")
        name, cmem = out
        if name == FALLBACK:
            return FALLBACK, (cmem, mems)
        if name not in self.index:
            raise ValueError(f"select eligió {name!r}, que no es una regla de {self.states} (ni FALLBACK)")
        i = self.index[name]
        if name != active or view.done(name):  # entra, o vuelve a entrar tras terminar: nuevo compromiso
            mems = mems[:i] + (_call(self.rules[i], "start", mems[i], partial, mems[i]),) + mems[i + 1:]
        if not self.propose(name, partial, mems[i]):
            return FALLBACK, (cmem, mems)
        return name, (cmem, mems)

    def score(self, partial, state, memory, action) -> float:
        _, mems = memory
        ranked = self.propose(state, partial, mems[self.index[state]])
        try:
            return float(ranked.index(action))
        except ValueError:
            return FAR

    def update(self, partial, state, memory, action):
        cmem, mems = memory
        i = self.index[state]
        rule = self.rules[i]
        new = _call(rule, "update", mems[i], partial, mems[i], action)
        return (cmem, mems[:i] + (new,) + mems[i + 1:])


class NoTransitions:
    """El controlador de la máquina mínima: sin reglas, todo lo decide el comodín."""

    def select(self, partial, memory, rules):
        return FALLBACK, memory


def rule_quality(policy: Any, view: Any, oracle, max_steps: int = 20_000) -> dict | None:
    """Con un oráculo exacto, por regla a lo largo de la construcción greedy: en cuántos pasos
    aplica (cobertura) y en cuántos de esos su primera propuesta es óptima (precisión). Dice si una
    regla está mal (propone mal cuando aplica) o mal usada (buena pero el controlador no la elige).
    None si el oráculo no alcanza aquí."""
    machine = getattr(policy, "machine", None)
    if not isinstance(machine, RuleMachine):
        return None
    partial = view.empty()
    d = oracle(partial)
    if d is None:
        return None
    memory = policy.init(partial)
    out = {n: {"applies": 0, "optimal": 0, "chosen": 0} for n in machine.states}
    steps = 0
    for _ in range(max_steps):
        if view.is_complete(partial):
            break
        cands = list(view.candidates(partial))
        if not cands:
            break
        state, (cmem, mems) = policy.step(partial, memory)
        rv = RuleView(machine, partial, mems, state if state in machine.index else None)
        for n in machine.states:
            prop = [a for a in rv.proposal(n) if a in cands]
            if prop:
                out[n]["applies"] += 1
                dn = oracle(view.apply(partial, prop[0]))
                if dn is None:
                    return None
                out[n]["optimal"] += dn == d - 1
        if state in out:
            out[state]["chosen"] += 1
        scores = [policy.score(partial, memory, c) for c in cands]
        a = cands[min(range(len(cands)), key=scores.__getitem__)]
        memory = policy.update(partial, memory, a)
        partial = view.apply(partial, a)
        d = oracle(partial)
        if d is None:
            return None
        steps += 1
    return {"steps": steps, "rules": out}


__all__ = ["RuleMachine", "RuleView", "NoTransitions", "rule_quality", "FAR"]
