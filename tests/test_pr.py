"""El slot relink (path relinking): el validador revisa su contrato. Los esqueletos PR de Python y de C++ se prueban
con el catálogo generado en `tests/test_native.py`."""

from random import Random

from core.validation.base import ValidationContext
from core.validation.pipeline import validate_component
from examples.jobshop import model_parts as mp
from examples.jobshop.pack import PACK

COMP = {"name": "machine_order", "slot": "relink", "compatible_skeletons": ["PR"], "params": {}}


class OrderRelink:
    """Distancia: pares de trabajos que dos soluciones ordenan distinto en alguna máquina; un paso intercambia dos
    trabajos consecutivos que están al revés que en la guía (baja la distancia en exactamente 1)."""

    def __init__(self, problem):
        pass

    def distance(self, a, b) -> int:
        d = 0
        for sa, sb in zip(a, b):
            pos = {j: i for i, j in enumerate(sb)}
            d += sum(pos[sa[i]] > pos[sa[k]] for i in range(len(sa)) for k in range(i + 1, len(sa)))
        return d

    def step(self, cur, guide, rng: Random):
        inv = []
        for m, (s, g) in enumerate(zip(cur, guide)):
            pos = {j: i for i, j in enumerate(g)}
            inv += [(m, i) for i in range(len(s) - 1) if pos[s[i]] > pos[s[i + 1]]]
        if not inv:
            return cur
        m, i = inv[rng.randrange(len(inv))]
        seqs = [list(s) for s in cur]
        seqs[m][i], seqs[m][i + 1] = seqs[m][i + 1], seqs[m][i]
        return mp.canonical(seqs)


def test_relink_contract():
    inst = PACK.make_instances(1, 5, PACK.parse_size("5x4"))[0]
    ctx = ValidationContext(problem=PACK.problem_factory(inst), instances=[inst], trivial_solutions=[mp.trivial_solution(inst)])
    assert validate_component(COMP, OrderRelink(ctx.problem), ctx).passed

    class Stuck(OrderRelink):
        def step(self, cur, guide, rng):
            return cur

    rep = validate_component(COMP, Stuck(ctx.problem), ctx)
    assert not rep.passed and "relink.path" in rep.feedback()
