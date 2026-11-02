"""El PFSP con flowtime total: instancias de Taillard, mejores conocidas y el modelo de referencia contra sus casos."""

import json
from pathlib import Path

from core.validation.model_parts import check_heuristic_view
from examples.flowshop import model_parts as ref
from examples.flowshop.instance import PFSPInstance
from examples.flowshop.pack import PACK


def test_reference_passes_its_cases():
    assert check_heuristic_view(ref, PACK.load_cases()).passed


def test_taillard_instances_and_best_known():
    d = Path("examples/flowshop/taillard")
    bk = {k: v for k, v in json.loads((d / "best_known.json").read_text()).items() if not k.startswith("_")}
    assert len(bk) == 120 and bk["tai20_5_0"] == 14033
    inst = PFSPInstance.load(str(d / "tai20_5_0.txt"))
    assert (inst.n_jobs, inst.n_machines) == (20, 5) and PFSPInstance.parse(inst.to_text()) == inst
    # ninguna permutación puede bajar de la mejor conocida (óptima en ta001); la identidad queda arriba
    assert ref.cost_terms(inst, ref.trivial_solution(inst))["flowtime"] > bk["tai20_5_0"]


def test_instance_save_roundtrip(tmp_path):
    from random import Random

    from examples.flowshop.instance import PFSPInstance

    inst = PFSPInstance.random(7, 3, Random(1))
    inst.save(str(tmp_path / "i.txt"))
    assert PFSPInstance.load(str(tmp_path / "i.txt")) == inst


def test_mixed_sizes_and_budget_scale(tmp_path):
    from examples.flowshop.pack import PACK
    from tuning.cli import mixed_instances
    from tuning.irace_scenario import write_irace_scenario
    from tuning.cli import make_assembler

    insts = mixed_instances(PACK, "8x3,12x4", 5, 0)
    assert [(i.n_jobs, i.n_machines) for i in insts] == [(8, 3)] * 3 + [(12, 4)] * 2
    assert mixed_instances(PACK, "8x3", 2, 0) == PACK.make_instances(2, 0, PACK.parse_size("8x3"))
    assert PACK.budget_scale(PACK.make_instances(1, 0, PACK.parse_size("100x20"))[0]) == 4.0

    assembler, _ = make_assembler(PACK, "generated", "generated/flowshop_native", native=True, scale_budget=True)
    seen = []
    assembler.assemble = lambda config: (lambda inst, rng, budget: seen.append(budget) or (_ for _ in ()).throw(RuntimeError()))
    assembler.evaluate({}, [insts[3]], 2.0)  # el runner falla a propósito: solo interesa el presupuesto
    assert seen == [2.0 * 12 * 4 / 500]

    space = assembler.config_space()
    write_irace_scenario(space, tmp_path, [], 1.0, scale_budget=True)
    assert "HSF_SCALE_BUDGET=1" in (tmp_path / "target-runner").read_text()
