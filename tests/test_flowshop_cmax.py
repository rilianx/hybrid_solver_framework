"""El PFSP con makespan: mismas instancias de Taillard, sus mejores conocidas y el modelo de referencia contra sus casos."""

import json
from pathlib import Path

from core.validation.model_parts import check_heuristic_view
from examples.flowshop.instance import PFSPInstance
from examples.flowshop_cmax import model_parts as ref
from examples.flowshop_cmax.pack import PACK


def test_reference_passes_its_cases():
    assert check_heuristic_view(ref, PACK.load_cases()).passed


def test_makespan_and_best_known():
    bk = {k: v for k, v in json.loads(Path("examples/flowshop_cmax/best_known.json").read_text()).items()
          if not k.startswith("_")}
    assert len(bk) == 120 and bk["tai20_5_0"] == 1278
    inst = PFSPInstance.load("examples/flowshop/taillard/tai20_5_0.txt")
    trivial = ref.cost_terms(inst, ref.trivial_solution(inst))["makespan"]
    # cota inferior: la carga de cualquier máquina; la identidad queda arriba de la mejor conocida
    assert max(sum(row) for row in inst.p) <= bk["tai20_5_0"] < trivial
    # makespan en una instancia de 2 máquinas a mano: p0 = (3, 1), p1 = (2, 4)
    tiny = PFSPInstance(((3, 1), (2, 4)))
    assert ref.cost_terms(tiny, ((0, 1),))["makespan"] == 9 and ref.cost_terms(tiny, ((1, 0),))["makespan"] == 7


def test_pack_contexts_and_eval_problem():
    assert PACK.name == "flowshop_cmax" and PACK.budget_scale(PACK.make_instances(1, 0, PACK.parse_size("100x20"))[0]) == 4
    assert PACK.make_contexts()
