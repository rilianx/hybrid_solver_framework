"""Máquinas de reglas: reglas simples y macros con prioridad (lo que genera y evoluciona el LLM).

Una heurística constructiva como FRG no puntúa todos los candidatos: tiene REGLAS que, de las
acciones posibles, eligen un subconjunto y un orden, y una prioridad entre ellas.

    class ReglaSimple:                                 # p.ej. bg_move: se reevalúa en cada paso
        name = "bg_move"
        priority = 100                                 # mayor = se prefiere
        allowed(parcial, memoria, candidatos) -> [acciones]  # subconjunto de candidatos; [] = no aplica
        score(parcial, memoria, acción) -> float       # opcional (menor = mejor); si no, el orden de allowed
        init(parcial) -> memoria                       # opcional (default ())
        update(parcial, memoria, acción) -> memoria    # opcional: tras hacer una de sus acciones

    class Macro(ReglaSimple):                          # p.ej. reduce_stack: un compromiso de varios pasos
        start(parcial, memoria) -> memoria             # al activarse: fija su parámetro (la pila a reducir)
        done(parcial, memoria) -> bool                 # ¿terminó el compromiso?

Una macro es un movimiento grande que se ejecuta de a un paso: se activa en un estado (`start`),
restringe las acciones posibles (`allowed`, con la memoria que fijó `start`), elige entre ellas
(`score`) y dice cuándo termina (`done`). Es una regla con `start` o `done`.

El controlador es fijo, sin código del LLM:

    si la regla activa es una macro que no terminó y tiene acciones permitidas: sigue
    si no: la de mayor prioridad con acciones permitidas (una macro se consulta como si empezara)
    si ninguna: el comodín `FALLBACK` (la acción que menos sube la cota inferior de la vista)

FRG son `bg_move` (simple, prioridad 100) y `reduce_stack` (macro, 50).

`RuleMachine(problem, reglas)` es una `ConstructionMachine` (estados = nombres de las reglas): el
greedy, la beam search, la validación, los parámetros y el diagnóstico por estado de
`core.machine` la usan sin cambios. Necesita las acciones posibles de cada parcial: la vista con
la que se construye se enlaza con `bind(view)` (lo hacen el greedy, la beam search y los
diagnósticos); sin enlazar, usa `problem.construction_view(problem.inst)`. Un candidato que la
regla activa no permite vale `FAR` (más la cota, para desempatar).

`llm.evolve` agrega reglas simples o macros, refina una regla sin tocar las otras y cambia
prioridades. Con un oráculo, `rule_quality` da por regla cobertura (en cuántos pasos aplica) y
precisión (cuando aplica, qué fracción de las veces su primera acción es óptima).
"""

from __future__ import annotations

from typing import Any, Sequence

from .machine import FALLBACK, FAR


def action_key(a: Any):
    """La acción por su valor: un dataclass o una tupla con nombre valen por sus campos. Corrida 71:
    la regla definía su propio `Move = namedtuple(...)`, que nunca es igual al `Move` (dataclass) de
    la vista."""
    import dataclasses

    if dataclasses.is_dataclass(a) and not isinstance(a, type):
        return tuple(getattr(a, f.name) for f in dataclasses.fields(a))
    if isinstance(a, tuple):
        return tuple(a)
    return a


def _call(obj, name, default, *args):
    fn = getattr(obj, name, None)
    return default if fn is None else fn(*args)


def is_macro(rule: Any) -> bool:
    return callable(getattr(rule, "start", None)) or callable(getattr(rule, "done", None))


class RuleMachine:
    """Reglas simples y macros con prioridad como `ConstructionMachine`. Memoria: la de cada regla."""

    def __init__(self, problem: Any, rules: Sequence[Any]):
        self.problem = problem
        self.rules = list(rules)
        names = [getattr(r, "name", None) for r in self.rules]
        if any(not isinstance(n, str) for n in names) or len(set(names)) != len(names):
            raise ValueError(f"cada regla necesita un `name` (str) distinto; hay {names}")
        for r in self.rules:
            p = getattr(r, "priority", 100)
            if isinstance(p, bool) or not isinstance(p, (int, float)):
                raise ValueError(f"la prioridad de `{r.name}` debe ser un número, no {p!r}")
            if not callable(getattr(r, "allowed", None)):
                raise ValueError(f"la regla `{r.name}` necesita `allowed(parcial, memoria, candidatos)`")
        self.states = tuple(names)
        self.index = {n: i for i, n in enumerate(names)}
        # por prioridad (mayor primero); a igual prioridad, el orden de la lista
        self.order = sorted(range(len(self.rules)), key=lambda i: -float(getattr(self.rules[i], "priority", 100)))
        self._view = None  # la vista enlazada (bind) o (instancia, vista) propia
        self._bound = False
        self._cands: tuple | None = None  # (parcial, candidatos)
        self._cache: tuple | None = None  # (parcial, regla, memoria, permitidas)

    # --- acciones posibles ---------------------------------------------------------------
    def bind(self, view: Any) -> None:
        """La vista con la que se construye: de ella salen las acciones posibles de cada parcial."""
        self._view, self._bound, self._cands, self._cache = view, True, None, None

    def view(self):
        if self._bound:
            return self._view
        inst = getattr(self.problem, "inst", None)
        if self._view is None or self._view[0] is not inst:
            self._view = (inst, self.problem.construction_view(inst))
        return self._view[1]

    def candidates(self, partial) -> list:
        c = self._cands
        if c is not None and c[0] is partial:
            return c[1]
        out = list(self.view().candidates(partial))
        self._cands = (partial, out)
        return out

    def allowed(self, name: str, partial: Any, mem: Any) -> list:
        """Las acciones que la regla permite, filtradas a los candidatos (por valor, en su orden)."""
        c = self._cache
        if c is not None and c[0] is partial and c[1] == name and c[2] == mem:
            return c[3]
        cands = self.candidates(partial)
        by_key = {}
        for x in cands:
            by_key.setdefault(action_key(x), x)
        out, seen = [], set()
        for a in self.rules[self.index[name]].allowed(partial, mem, cands) or []:
            k = action_key(a)
            if k in by_key and k not in seen:
                seen.add(k)
                out.append(by_key[k])
        self._cache = (partial, name, mem, out)
        return out

    def entry(self, name: str, partial: Any, mem: Any):
        """La memoria de la regla si se activara ahora (una macro empieza)."""
        rule = self.rules[self.index[name]]
        return _call(rule, "start", mem, partial, mem) if is_macro(rule) else mem

    # --- ConstructionMachine ----------------------------------------------------------------
    def initial(self, partial):
        return FALLBACK, tuple(_call(r, "init", (), partial) for r in self.rules)

    def transition(self, partial, state, memory):
        mems = memory
        if state in self.index:
            i = self.index[state]
            rule = self.rules[i]
            if is_macro(rule) and not _call(rule, "done", True, partial, mems[i]) and self.allowed(state, partial, mems[i]):
                return state, mems
        for i in self.order:
            name = self.rules[i].name
            mem = self.entry(name, partial, mems[i])
            if self.allowed(name, partial, mem):
                return name, mems[:i] + (mem,) + mems[i + 1:]
        return FALLBACK, mems

    def score(self, partial, state, memory, action) -> float:
        i = self.index[state]
        ranked = self.allowed(state, partial, memory[i])
        keys = self._keys(ranked)
        k = action_key(action)
        if k not in keys:
            return FAR
        rule = self.rules[i]
        if callable(getattr(rule, "score", None)):
            return float(rule.score(partial, memory[i], action))
        return float(keys[k])

    def _keys(self, ranked: list) -> dict:
        c = getattr(self, "_keys_cache", None)
        if c is not None and c[0] is ranked:
            return c[1]
        keys: dict = {}
        for i, a in enumerate(ranked):
            keys.setdefault(action_key(a), i)
        self._keys_cache = (ranked, keys)
        return keys

    def update(self, partial, state, memory, action):
        i = self.index[state]
        new = _call(self.rules[i], "update", memory[i], partial, memory[i], action)
        return memory[:i] + (new,) + memory[i + 1:]


def rule_breadth(policy: Any, view: Any, max_steps: int = 20_000) -> dict | None:
    """Por regla, a lo largo de la construcción greedy: en cuántos pasos permite algo y en cuántos
    permite TODOS los candidatos. Una regla que casi siempre permite todo es un puntaje compuesto
    disfrazado de regla (corridas 72–75: la primera regla del LLM ordenaba todos los movimientos
    por una suma ponderada); partirla en varias reglas con prioridad (un tipo de movimiento cada
    una) es lo que hace FRG. No se rechaza: se informa y `llm.evolve` propone partirla."""
    machine = getattr(policy, "machine", None)
    if not isinstance(machine, RuleMachine):
        return None
    policy.bind(view)
    partial = view.empty()
    memory = policy.init(partial)
    out = {n: {"applies": 0, "all": 0} for n in machine.states}
    for _ in range(max_steps):
        if view.is_complete(partial):
            break
        cands = list(view.candidates(partial))
        if not cands:
            break
        state, mems = policy.step(partial, memory)
        for n in machine.states:
            i = machine.index[n]
            mem = mems[i] if n == state else machine.entry(n, partial, mems[i])
            k = len(machine.allowed(n, partial, mem))
            if k:
                out[n]["applies"] += 1
                out[n]["all"] += k == len(cands) and len(cands) > 1
        scores = [policy.score(partial, memory, c) for c in cands]
        a = cands[min(range(len(cands)), key=scores.__getitem__)]
        memory = policy.update(partial, memory, a)
        partial = view.apply(partial, a)
    return out


def rule_quality(policy: Any, view: Any, oracle, max_steps: int = 20_000) -> dict | None:
    """Con un oráculo exacto, por regla a lo largo de la construcción greedy: en cuántos pasos
    aplica (cobertura) y en cuántos de esos su primera acción es óptima (precisión). Dice si una
    regla está mal (elige mal cuando aplica) o mal usada (buena pero con poca prioridad). None si
    el oráculo no alcanza aquí."""
    machine = getattr(policy, "machine", None)
    if not isinstance(machine, RuleMachine):
        return None
    policy.bind(view)
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
        state, mems = policy.step(partial, memory)
        for n in machine.states:
            i = machine.index[n]
            mem = mems[i] if n == state else machine.entry(n, partial, mems[i])
            ranked = machine.allowed(n, partial, mem)
            if ranked:
                rule = machine.rules[i]
                if callable(getattr(rule, "score", None)):
                    ranked = sorted(ranked, key=lambda a: rule.score(partial, mem, a))
                out[n]["applies"] += 1
                dn = oracle(view.apply(partial, ranked[0]))
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


__all__ = ["RuleMachine", "is_macro", "rule_breadth", "rule_quality", "action_key", "FAR"]
