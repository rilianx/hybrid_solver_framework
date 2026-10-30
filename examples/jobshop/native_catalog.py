"""El catálogo escrito a mano del job shop en C++, envuelto con la interfaz de los slots de Python: lo
que el validador de componentes prueba. Mismos nombres que `catalog.HANDWRITTEN`."""

from __future__ import annotations

from random import Random

from .native_parts import model, native


class NativeConstructor:
    def __init__(self, problem, name, **params):
        self.h = native.make_constructor(model(problem.inst), name, params)

    def build(self, inst, rng: Random):
        return self.h.build(rng.getrandbits(63))


class NativeNeighborhood:
    def __init__(self, problem, name, **params):
        self.h = native.make_neighborhood(model(problem.inst), name, params)
        if self.h.has_estimate():  # solo si el componente C++ la define (la usa TS)
            self.estimate = self.h.estimate

    def moves(self, sol):
        return self.h.moves(sol)

    def apply(self, sol, m):
        return self.h.apply(sol, m)

    def delta(self, sol, m):
        return self.h.delta(sol, m)


class NativePerturbation:
    def __init__(self, problem, name, **params):
        self.h = native.make_perturbation(model(problem.inst), name, params)

    def perturb(self, sol, strength, rng: Random):
        return self.h.perturb(sol, float(strength), rng.getrandbits(63))


_WRAP = {"constructor": NativeConstructor, "neighborhood": NativeNeighborhood, "perturbation": NativePerturbation}


def native_handwritten() -> list:
    """`catalog.HANDWRITTEN` con los componentes nativos en los slots que corre C++ (los puntajes y las
    destrucciones siguen en Python: los primeros los usa el constructor greedy nativo por nombre)."""
    from .catalog import HANDWRITTEN

    out = []
    names = native.names()
    for comp, factory in HANDWRITTEN:
        slot = comp["slot"]
        if slot in _WRAP and comp["name"] in names[slot]:
            factory = (lambda cls, name: lambda problem, **kw: cls(problem, name, **kw))(_WRAP[slot], comp["name"])
        out.append((comp, factory))
    return out
