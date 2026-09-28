"""Máquinas de estados constructivas (slot `construction_machine`).

Muchas heurísticas constructivas cambian su forma de construir según el estado de la
construcción. FRG en el CPMP tiene dos estados:

    LLENAR  --(no queda movimiento BG)-->                 REDUCIR(sr)   [al entrar: elegir sr]
    REDUCIR --(sr vacía, u ordenada y criterio de parada)-->  LLENAR (si hay BG) o REDUCIR(otra sr)

En cada estado se construye con una regla distinta, y el algoritmo son esas reglas junto con
las transiciones. El LLM escribe la máquina completa en un solo módulo: estados, regla de cada
uno y transiciones se diseñan juntos. El framework la corre:

    class ConstructionMachine:
        states: tuple[str, ...]
        initial(partial) -> (estado, memoria)
        transition(partial, estado, memoria) -> (estado, memoria)   # antes de cada paso
        score(partial, estado, memoria, acción) -> float            # MENOR = mejor
        update(partial, estado, memoria, acción) -> memoria         # tras la acción

`MachinePolicy(máquina)` es una `construction_policy`: la memoria de la política es
(estado, memoria de la máquina), y la usan igual el greedy y la beam search. En cada paso:

    estado, memoria ← transition(parcial, estado, memoria)   # "bajo ciertas condiciones se pasa a otro estado"
    puntaje de cada candidato = score(parcial, estado, memoria, ·)
    memoria ← update(parcial, estado, memoria, acción elegida)

Estado comodín `FALLBACK` ("_default"): una máquina puede devolverlo desde `transition` cuando
ninguno de sus estados sabe qué hacer; no se declara en `states` y lo resuelve el framework
(`LowerBoundScore`: la acción que menos sube la cota inferior de la vista, o la primera si la vista
no da cota). Así una máquina a medio construir ("solo movimientos BG") ya es un constructor
completo, y la etapa `evolve` puede partir de ahí e ir agregando estados.

Los números que deciden algo (umbrales de una transición, pesos, desempates) son parámetros
del componente (`COMPONENT["params"]`, con rango y default): entran al espacio del tuner junto
con los demás hiperparámetros (`greedy_<máquina>`, `beam_<máquina>`). La validación rechaza
constantes sueltas en el código generado y parámetros declarados que no cambian nada.
"""

from __future__ import annotations

from typing import Any

FALLBACK = "_default"


class LowerBoundScore:
    """La regla del estado comodín: la acción cuyo parcial siguiente tiene la menor cota inferior
    (`view.lower_bound`); sin cota, todas valen lo mismo (decide el orden de la vista). Es la
    regla más neutral que da la vista: no sabe nada del problema salvo su cota."""

    def __init__(self, problem: Any = None):
        self.problem = problem
        self._view: tuple | None = None  # (instancia, vista)

    def _get_view(self):
        inst = getattr(self.problem, "inst", None)
        if self.problem is None or inst is None or not callable(getattr(self.problem, "construction_view", None)):
            return None
        if self._view is None or self._view[0] is not inst:
            self._view = (inst, self.problem.construction_view(inst))
        return self._view[1]

    def score(self, partial, action) -> float:
        view = self._get_view()
        lb = getattr(view, "lower_bound", None)
        if not callable(lb):
            return 0.0
        return float(lb(view.apply(partial, action)))


class MachinePolicy:
    """Una `ConstructionMachine` vista como `construction_policy`. `problem`: para la regla del
    estado comodín (`FALLBACK`)."""

    def __init__(self, machine: Any, problem: Any = None):
        self.machine = machine
        self.states = tuple(machine.states)
        self.fallback = LowerBoundScore(problem if problem is not None else getattr(machine, "problem", None))
        self._cache: tuple | None = None  # (parcial, memoria, transición): score se llama por candidato

    def init(self, partial):
        state, memory = self.machine.initial(partial)
        return (state, memory)

    def step(self, partial: Any, memory: tuple) -> tuple[str, Any]:
        """(estado, memoria) con los que se elige la acción en `partial`: tras la transición."""
        c = self._cache
        if c is not None and c[0] is partial and c[1] == memory:
            return c[2]
        state, mem = memory
        out = self.machine.transition(partial, state, mem)
        if not (isinstance(out, tuple) and len(out) == 2):
            raise TypeError(f"transition debe devolver (estado, memoria), no {out!r}")
        if out[0] not in self.states and out[0] != FALLBACK:
            raise ValueError(f"transition devolvió el estado {out[0]!r}, que no está en states {self.states} (ni es "
                             f"el comodín {FALLBACK!r})")
        self._cache = (partial, memory, out)
        return out

    def score(self, partial, memory, action) -> float:
        state, mem = self.step(partial, memory)
        if state == FALLBACK:
            return self.fallback.score(partial, action)
        return self.machine.score(partial, state, mem, action)

    def update(self, partial, memory, action):
        state, mem = self.step(partial, memory)
        if state == FALLBACK:
            return (state, mem)
        return (state, self.machine.update(partial, state, mem, action))

    def state_of(self, partial, memory) -> str:
        return self.step(partial, memory)[0]


def machine_trace(policy: MachinePolicy, view: Any, max_steps: int = 100_000) -> list[tuple[str, Any]]:
    """Construye con el greedy de la máquina y devuelve [(estado, acción)] paso a paso: para los
    diagnósticos (cuántos pasos en cada estado, qué transiciones hubo, dónde se pierde)."""
    partial, out = view.empty(), []
    memory = policy.init(partial)
    for _ in range(max_steps):
        if view.is_complete(partial):
            break
        cands = list(view.candidates(partial))
        if not cands:
            break
        scores = [policy.score(partial, memory, c) for c in cands]
        a = cands[min(range(len(cands)), key=scores.__getitem__)]
        out.append((policy.state_of(partial, memory), a))
        memory = policy.update(partial, memory, a)
        partial = view.apply(partial, a)
    return out


def machine_profile(policy: MachinePolicy, view: Any, max_steps: int = 100_000) -> dict[str, dict]:
    """Por estado: pasos, cota inferior perdida (Σ del aumento de `view.lower_bound` en sus pasos) y
    pasos que la hacen subir. Con una cota exacta al completar, la suma sobre los estados es
    objetivo − cota inicial: cuánto de lo que se pierde es culpa de cada estado. Sin cota, solo
    los pasos."""
    lb = getattr(view, "lower_bound", None)
    lb = lb if callable(lb) else None
    partial = view.empty()
    memory = policy.init(partial)
    out: dict[str, dict] = {}
    for _ in range(max_steps):
        if view.is_complete(partial):
            break
        cands = list(view.candidates(partial))
        if not cands:
            break
        scores = [policy.score(partial, memory, c) for c in cands]
        a = cands[min(range(len(cands)), key=scores.__getitem__)]
        state = policy.state_of(partial, memory)
        memory = policy.update(partial, memory, a)
        nxt = view.apply(partial, a)
        row = out.setdefault(state, {"steps": 0, "lost": 0.0, "rising": 0})
        row["steps"] += 1
        if lb is not None:
            d = float(lb(nxt)) - float(lb(partial))
            row["lost"] += max(0.0, d)
            row["rising"] += d > 1e-9
        partial = nxt
    return out


def compress_trace(steps: list[tuple[str, Any]], max_steps: int = 60) -> str:
    """`estado: acciones` por tramo, para un prompt."""
    lines, cur, run = [], None, []
    for name, a in steps[:max_steps]:
        if name != cur and run:
            lines.append(f"{cur}: {', '.join(run)}")
            run = []
        cur = name
        run.append(repr(a))
    if run:
        lines.append(f"{cur}: {', '.join(run)}")
    more = f"\n… ({len(steps) - max_steps} pasos más)" if len(steps) > max_steps else ""
    return "\n".join(lines) + more + f"\n(total: {len(steps)} pasos)"


__all__ = ["FALLBACK", "LowerBoundScore", "MachinePolicy", "machine_trace", "machine_profile", "compress_trace"]
