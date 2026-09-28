"""Construcción por fases: una política constructiva armada con varias fases (slot `phase`).

Muchas heurísticas constructivas no son un puntaje único sino un programa chico con modos:
FRG en el CPMP alterna "llenar" (un movimiento que deja bien puesto un mal puesto, elegido
de nuevo en cada paso) con "reducir una pila" (elegir una pila y vaciarla hasta un criterio de
parada, sosteniendo esa decisión varios pasos). Escribir eso como un solo `construction_policy`
obliga a meter todo en un puntaje y una tupla de memoria (corrida 62: las políticas generadas
hacían eso a mano y quedaban débiles como greedy). Con fases, cada modo es una pieza chica:

    class Phase:
        init(partial) -> memoria                     # memoria propia de la fase (hashable)
        applies(partial, memoria) -> bool            # ¿puede tomar el control ahora?
        start(partial, memoria) -> memoria           # opcional: al tomar el control (p.ej. elegir la pila)
        score(partial, memoria, acción) -> float     # MENOR = mejor, entre los candidatos de la vista
        update(partial, memoria, acción) -> memoria  # tras hacer la acción que eligió
        done(partial, memoria) -> bool               # opcional: ¿suelta el control? (default: tras cada paso)

`PhasedPolicy([f1, ..., fk])` es una `construction_policy` (la usan igual el greedy y la beam
search). En cada paso:

    si la fase activa i no terminó (not fi.done(parcial, mi)): sigue i
    si no: la primera fase, en orden de prioridad, que applies → start → activa
           si ninguna aplica: la última (hace de comodín)
    puntaje de cada candidato = score de la fase activa

La cantidad de fases y su orden no son fijos: el tuner elige cuántas y cuáles (`greedy_phased`,
`beam_phased` en `llm.catalog`). Solo actúa la fase activa: su memoria cambia con `start` y
`update`; la de las demás queda como está hasta que vuelvan a tomar el control.
"""

from __future__ import annotations

from typing import Any, Sequence


def _applies(phase: Any, partial: Any, memory: Any) -> bool:
    fn = getattr(phase, "applies", None)
    return True if fn is None else bool(fn(partial, memory))


def _done(phase: Any, partial: Any, memory: Any) -> bool:
    fn = getattr(phase, "done", None)
    return True if fn is None else bool(fn(partial, memory))


def _start(phase: Any, partial: Any, memory: Any) -> Any:
    fn = getattr(phase, "start", None)
    return memory if fn is None else fn(partial, memory)


class NullPhase:
    """Fase sin criterio: siempre aplica y puntúa todo igual (decide el orden de la vista). Es la
    referencia contra la que se mide lo que aporta una fase."""

    COMPONENT = {"name": "null_phase", "slot": "phase", "params": {}}

    def init(self, partial):
        return ()

    def score(self, partial, memory, action) -> float:
        return 0.0

    def update(self, partial, memory, action):
        return memory


class PhasedPolicy:
    """`construction_policy` hecha de fases. Memoria: (índice de la fase activa o None, tupla con la
    memoria de cada fase). `names` es solo para los diagnósticos."""

    def __init__(self, phases: Sequence[Any], names: Sequence[str] | None = None):
        if not phases:
            raise ValueError("PhasedPolicy necesita al menos una fase")
        self.phases = list(phases)
        self.names = list(names) if names is not None else [type(p).__name__ for p in self.phases]
        self._cache: tuple | None = None  # (parcial, memoria, selección): score se llama por candidato

    def init(self, partial):
        return (None, tuple(p.init(partial) for p in self.phases))

    def select(self, partial: Any, memory: tuple) -> tuple[int, tuple]:
        """(fase que actúa en `partial`, memorias tras su `start` si recién toma el control)."""
        c = self._cache
        if c is not None and c[0] is partial and c[1] == memory:
            return c[2]
        active, mems = memory
        if active is not None and not _done(self.phases[active], partial, mems[active]):
            out = (active, mems)
        else:
            last = len(self.phases) - 1
            i = next((j for j, p in enumerate(self.phases) if _applies(p, partial, mems[j])), last)
            m = _start(self.phases[i], partial, mems[i])
            out = (i, mems[:i] + (m,) + mems[i + 1:])
        self._cache = (partial, memory, out)
        return out

    def score(self, partial, memory, action) -> float:
        i, mems = self.select(partial, memory)
        return self.phases[i].score(partial, mems[i], action)

    def update(self, partial, memory, action):
        i, mems = self.select(partial, memory)
        m = self.phases[i].update(partial, mems[i], action)
        return (i, mems[:i] + (m,) + mems[i + 1:])

    def active_name(self, partial, memory) -> str:
        return self.names[self.select(partial, memory)[0]]


def alone(phase: Any) -> PhasedPolicy:
    """Una fase sola, para validarla: la fase con `NullPhase` de comodín para cuando no aplica."""
    return PhasedPolicy([phase, NullPhase()], names=["fase", "null_phase"])


def phase_trace(policy: PhasedPolicy, view: Any, max_steps: int = 100_000) -> list[tuple[str, Any]]:
    """Construye con el greedy de `policy` y devuelve [(fase activa, acción)] paso a paso: para
    diagnosticar (cuántos pasos hizo cada fase, dónde se pierden movimientos)."""
    partial, memory, out = view.empty(), None, []
    memory = policy.init(partial)
    for _ in range(max_steps):
        if view.is_complete(partial):
            break
        cands = list(view.candidates(partial))
        if not cands:
            break
        scores = [policy.score(partial, memory, c) for c in cands]
        a = cands[min(range(len(cands)), key=scores.__getitem__)]
        out.append((policy.active_name(partial, memory), a))
        memory = policy.update(partial, memory, a)
        partial = view.apply(partial, a)
    return out


__all__ = ["PhasedPolicy", "NullPhase", "alone", "phase_trace"]
