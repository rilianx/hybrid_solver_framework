"""Máquinas de estados constructivas (slot `construction_machine`, `core.machine`): FRG es una
máquina de dos estados (llenar ↔ reducir); la validación exige estados alcanzables y parámetros
extraíbles (sin números sueltos, cada parámetro declarado con default y con efecto), y esos
parámetros entran al espacio del tuner con los demás hiperparámetros."""

from __future__ import annotations

from dataclasses import replace
from random import Random

import pytest

from config_space import suggest_from_space
from core.assembler import ALL_SKELETONS, Assembler
from core.beam_search import BeamSearchConstructor
from core.construction import GreedyConstructor
from core.machine import MachinePolicy, machine_trace
from core.validation import validate_component
from core.validation.params import loose_constants
from examples.cpmp.construction import FRGConstructor
from examples.cpmp.instance import CPMPInstance
from examples.cpmp.machine import FRGMachine
from examples.cpmp.problem_model import CPMPModel
from examples.lotsizing.random_search import RandomTrial

MACHINE_MODULE = '''
COMPONENT = {"name": "fill_then_unblock", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "requires": [],
             "params": {"max_gap": {"type": "int", "range": [0, 10], "default": 3},
                        "height_weight": {"type": "float", "range": [0.0, 5.0], "default": 1.0}}}


class FillThenUnblock:
    """fill: un contenedor mal puesto a una pila ordenada de grupo mayor o igual, con diferencia de
    grupos a lo más max_gap. Si no hay, unblock: elige la pila desordenada con menos contenedores
    bien puestos y le saca contenedores de encima hasta que quede ordenada."""

    states = ("fill", "unblock")

    def __init__(self, problem, max_gap=3, height_weight=1.0):
        self.max_gap, self.height_weight = max_gap, height_weight

    def _fill(self, L):
        out = {}
        for so in range(L.S):
            if not L.stacks[so] or L.is_sorted_stack(so):
                continue
            c = L.g(so)
            for sd in range(L.S):
                if sd != so and L.e(sd) > 0 and L.is_sorted_stack(sd) and L.g(sd) >= c and L.g(sd) - c <= self.max_gap:
                    out[(so, sd)] = L.g(sd) - c
        return out

    def initial(self, L):
        return "fill", (None,)

    def transition(self, L, state, memory):
        if self._fill(L):
            return "fill", (None,)
        t = memory[0]
        if state == "unblock" and t is not None and L.stacks[t] and not L.is_sorted_stack(t):
            return state, memory
        cands = [s for s in range(L.S) if L.stacks[s] and not L.is_sorted_stack(s)]
        return "unblock", (min(cands, key=lambda s: (L.sorted_n[s], s)) if cands else None,)

    def score(self, L, state, memory, a):
        if state == "fill":
            d = self._fill(L).get((a.so, a.sd))
            return 1e6 if d is None else float(d)
        if a.so != memory[0]:
            return 1e6
        c = L.g(a.so)
        good = L.is_sorted_stack(a.sd) and L.g(a.sd) >= c
        return (0 if good else 100) + self.height_weight * L.h(a.sd)

    def update(self, L, state, memory, a):
        return memory


def build_component(problem, max_gap=3, height_weight=1.0):
    return FillThenUnblock(problem, max_gap, height_weight)
'''

COMP = {"name": "m", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "params": {}}


@pytest.fixture(scope="module")
def contexts():
    from examples.cpmp.pack import PACK

    return [replace(c, diversity_probe=None) for c in PACK.make_contexts(strict=False)]


def _check(tmp_path, src, contexts, name="m"):
    from llm.generator import validate_generated_module

    path = tmp_path / f"{name}.py"
    path.write_text(src)
    return validate_generated_module(path, contexts)[0]


def test_frg_is_a_two_state_machine():
    same = 0
    for k in range(10):
        inst = CPMPInstance.cvs_like(5, 5, Random(k))
        P = CPMPModel(inst)
        same += GreedyConstructor(P, FRGMachine(P)).build(inst, Random(0)) == FRGConstructor(P, assignment="never").build(inst, Random(0))
    assert same == 10


def test_the_trace_shows_the_states_and_a_reduction_holds_its_stack():
    inst = CPMPInstance.cvs_like(5, 5, Random(3))
    P = CPMPModel(inst)
    trace = machine_trace(MachinePolicy(FRGMachine(P)), P.construction_view(inst))
    assert {s for s, _ in trace} == {"bg_move", "reduce_stack"}
    reduce_so = [a.so for s, a in trace if s == "reduce_stack"]
    assert len(set(reduce_so)) < len(reduce_so)


def test_beam_search_runs_the_machine():
    inst = CPMPInstance.cvs_like(5, 5, Random(1))
    P = CPMPModel(inst)
    g = P.objective(GreedyConstructor(P, FRGMachine(P)).build(inst, Random(0)))
    b = P.objective(BeamSearchConstructor(P, FRGMachine(P), beam_width=3, branching=10).build(inst, Random(0)))
    assert b <= g


def test_validation_accepts_frg_and_rejects_broken_machines(contexts):
    for c in contexts:
        r = validate_component(dict(COMP, name="frg_machine"), FRGMachine(c.problem), c)
        assert r.passed, r.feedback()

    from core.rules import RuleMachine
    from examples.cpmp.machine import BGMove, FRGTransitions, ReduceStack

    class Never:  # una regla que el controlador nunca elige
        name = "never"

        def propose(self, L, m):
            return []

    class BadChoice(FRGTransitions):
        def select(self, L, memory, rules):
            return "nope", memory

    c = contexts[0]
    unreachable = RuleMachine(c.problem, [BGMove(), ReduceStack(), Never()], FRGTransitions())
    assert "states_reachable" in validate_component(COMP, unreachable, c).feedback()
    assert not validate_component(COMP, RuleMachine(c.problem, [BGMove(), ReduceStack()], BadChoice()), c).passed


def test_generated_machines_expose_their_numbers_as_parameters(tmp_path, contexts):
    """El framework normaliza la máquina en vez de rechazarla: un número suelto en un método pasa a
    ser parámetro, uno sin default toma el de la firma, uno inerte sale de COMPONENT. Un número
    fuera de la clase (en una función de módulo) sigue siendo un rechazo."""
    import importlib.util

    def load(name):
        spec = importlib.util.spec_from_file_location(name, tmp_path / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    assert _check(tmp_path, MACHINE_MODULE, contexts).passed
    loose = MACHINE_MODULE.replace("L.g(sd) - c <= self.max_gap", "L.g(sd) - c <= 3")
    r = _check(tmp_path, loose, contexts, "loose")
    assert r.passed and "extraídos como parámetros" in r.feedback() + str(r.results)
    mod = load("loose")
    extracted = [p for p in mod.COMPONENT["params"] if p.startswith("fill_k")]
    assert extracted and mod.COMPONENT["params"][extracted[0]] == {"type": "int", "range": [0, 6], "default": 3}
    assert mod.build_component(contexts[0].problem, **{extracted[0]: 5})._auto_fill_k1 == 5  # el tuner lo mueve
    inert = (MACHINE_MODULE.replace('"default": 1.0}}}', '"default": 1.0}, "unused": {"type": "int", "range": [1, 4], "default": 2}}}')
             .replace("def build_component(problem, max_gap=3, height_weight=1.0):", "def build_component(problem, max_gap=3, height_weight=1.0, unused=2):"))
    assert _check(tmp_path, inert, contexts, "inert").passed
    assert "unused" not in load("inert").COMPONENT["params"]
    no_default = MACHINE_MODULE.replace('"range": [0, 10], "default": 3}', '"range": [0, 10]}')
    assert _check(tmp_path, no_default, contexts, "nodef").passed
    assert load("nodef").COMPONENT["params"]["max_gap"]["default"] == 3
    outside = MACHINE_MODULE.replace("class FillThenUnblock:", "def _gap_limit():\n    return 7\n\n\nclass FillThenUnblock:")
    assert "no_loose_constants" in _check(tmp_path, outside, contexts, "outside").feedback()


def test_what_counts_as_a_loose_constant():
    src = "COMPONENT = {'params': {'t': {'range': [0.1, 0.9]}}}\n\ndef f(x, t=0.3):\n    return x[-1] * 0.7 + 1e6 + 1000 * t + 1e-9 + 2\n"
    assert [v for _, v in loose_constants(src)] == [0.7]


def test_machine_parameters_enter_the_tuner_space(tmp_path, contexts):
    """Los parámetros que declara la máquina quedan en el espacio junto con la regla del greedy y
    el ancho de la beam search."""
    import importlib.util

    from examples.cpmp.pack import PACK
    from llm.catalog import build_registry
    from llm.generator import GeneratedComponent

    path = tmp_path / "fill_then_unblock_r1.py"
    path.write_text(MACHINE_MODULE)
    spec = importlib.util.spec_from_file_location("fill_then_unblock_r1", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    gen = [GeneratedComponent("fill_then_unblock", "construction_machine", path, MACHINE_MODULE, mod.COMPONENT, mod.build_component, rounds=1)]
    reg = build_registry(PACK, gen, handwritten=False)
    asm = Assembler(problem_factory=PACK.problem_factory, registry=reg, skeletons={"CONSTRUCT": ALL_SKELETONS["CONSTRUCT"]})
    names = {n.name for n in asm.config_space().nodes}
    assert {"greedy_fill_then_unblock.max_gap", "greedy_fill_then_unblock.height_weight", "greedy_fill_then_unblock.rule",
            "beam_fill_then_unblock.max_gap", "beam_fill_then_unblock.beam_width"} <= names
    space = asm.config_space()
    for seed in range(20):
        config = space.fold(suggest_from_space(space, RandomTrial(Random(seed))))
        if config.get("constructor") == "greedy_fill_then_unblock":
            inst = CPMPInstance.cvs_like(4, 4, Random(seed))
            assert asm.assemble(config)(inst, Random(0), 5.0).best_objective >= 0
            break
    else:
        raise AssertionError("el tuner nunca eligió la máquina")


def test_prompt_and_generation_of_a_machine(contexts, tmp_path):
    from examples.cpmp.pack import PACK
    from llm import ScriptedClient, generate_slot
    from llm.prompts import generation_prompt

    p = generation_prompt(PACK.make_spec(), "construction_machine", 2)
    assert "class ConstructionMachine(Protocol)" in p and "category_then_top_up" in p and "COMPONENT['params']" in p
    broken = MACHINE_MODULE.replace("states = (\"fill\", \"unblock\")", "states = [\"fill\", \"unblock\"]")  # states no es tupla
    client = ScriptedClient(responses=[f"```python\n{broken}\n```", f"```python\n{MACHINE_MODULE}\n```"])
    accepted, stats = generate_slot(client, PACK.make_spec(), "construction_machine", 1, contexts[:1], tmp_path, max_rounds=2,
                                    verbose=False)
    assert [c.name for c in accepted] == ["fill_then_unblock"], stats.rejections_by_layer
    assert "construction_machine.states" in client.calls[1][1]


def test_run65_candidate_passes_once_normalized(tmp_path, contexts):
    """Corrida 65: esta máquina (tal cual la escribió el LLM) se rechazó por un `10.0` y un `0.01`
    sueltos. Normalizada, el `10.0` es un parámetro del tuner y el `0.01` (sin efecto) queda fijo."""
    from pathlib import Path

    src = (Path(__file__).parent / "fixtures" / "run65_good_placement_state.py").read_text()
    r = _check(tmp_path, src, contexts, "run65")
    assert r.passed, r.feedback()
    text = (tmp_path / "run65.py").read_text()
    assert "self._auto_score_k1" in text and "'score_k1': {'type': 'float', 'range': [0.0, 20.0], 'default': 10.0}" in text


def test_the_protocol_accepts_states_as_a_data_attribute(monkeypatch):
    """Desde Python 3.12 `__protocol_attrs__` incluye `states`; exigirlo invocable rechazaba toda
    máquina en CI (corrida 65)."""
    from core import contracts
    from core.validation.syntactic import check_protocol

    monkeypatch.setattr(contracts.ConstructionMachine, "__protocol_attrs__",
                        {"states", "initial", "transition", "score", "update"}, raising=False)
    assert check_protocol("construction_machine", FRGMachine()).passed

    class NoStates:
        def initial(self, p): ...
        def transition(self, *a): ...
        def score(self, *a): ...
        def update(self, *a): ...

    assert "states" in check_protocol("construction_machine", NoStates()).message
