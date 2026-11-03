"""Conversión de las instancias de Trigeiro (LP de Zimpl, strIPlib) al formato del CLSP."""

from pathlib import Path

from examples.lotsizing.instance import CLSPInstance
from examples.lotsizing.trigeiro_convert import parse_lp

LP = """\\ comentario
Minimize
 cost:  +100 y#1#1 +50 y#1#2 +100 y#2#1 +50 y#2#2
  +2 s#1#1 +3 s#1#2 +2 s#2#1 +3 s#2#2
Subject to
 balance_1:
  - s#1#1 + x#1#1 = 10
 balance_2:
  - s#2#1 + s#1#1 + x#2#1 = 0
 balance_3:
  - s#1#2 + x#1#2 = 4
 balance_4:
  - s#2#2 + s#1#2 + x#2#2 = 6
 capacity_1:
  +5 y#1#1 +7 y#1#2 + x#1#1 +0.5 x#1#2
  <= 40
 capacity_2:
  +5 y#2#1 +7 y#2#2 + x#2#1 +0.5 x#2#2
  <= 40
Bounds
End
"""


def test_parse_lp_scales_unit_times():
    inst = parse_lp(LP)
    assert (inst.n_items, inst.n_periods) == (2, 2)
    assert inst.demand == ((10.0, 0.0), (2.0, 3.0))  # el ítem 2 en unidades de tiempo (alpha = 0.5)
    assert inst.setup_cost == (100.0, 50.0) and inst.setup_time == (5.0, 7.0)
    assert inst.holding_cost == (2.0, 6.0) and inst.capacity == (40.0, 40.0)


def test_converted_files_load():
    files = sorted(Path("examples/lotsizing/trigeiro").glob("*.txt"))
    assert len(files) == 75
    g72 = CLSPInstance.load("examples/lotsizing/trigeiro/G72.txt")
    assert (g72.n_items, g72.n_periods) == (24, 30)
