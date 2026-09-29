"""Etapa `evolve` (`llm.evolve`): un algoritmo de optimización chico sobre máquinas de reglas
(`core.rules.RuleMachine`). Operadores tipados con alcance verificado clase por clase, calendario
(agregar regla → refinarla), tuning corto de los parámetros dentro del loop, diagnóstico por regla
y archivo con nichos por cantidad de reglas."""

from __future__ import annotations

from random import Random

import pytest

from examples.cpmp.pack import PACK
from llm import ScriptedClient
from core.construction import GreedyConstructor
from llm.evolve import MINIMAL, Harness, Individual, admit, evolve, scope_check, tune
from tests.test_machine import MACHINE_MODULE

BG_ONLY = '''
COMPONENT = {"name": "bg_only", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "requires": [],
             "params": {}}

from core.machine import FALLBACK
from core.rules import RuleMachine
from examples.cpmp.construction import Move


class BG:
    \"\"\"Mover un mal puesto a una pila ordenada de grupo mayor o igual, la menor diferencia de grupos primero.\"\"\"

    name = "bg"

    def propose(self, L, memory):
        out = []
        for so in range(L.S):
            if L.stacks[so] and not L.is_sorted_stack(so):
                for sd in range(L.S):
                    if sd != so and L.e(sd) > 0 and L.is_sorted_stack(sd) and L.g(sd) >= L.g(so):
                        out.append((L.g(sd) - L.g(so), so, sd))
        return [Move(so, sd) for _, so, sd in sorted(out)]


class Trans:
    def select(self, L, memory, rules):
        return ("bg", memory) if rules.applies("bg") else (FALLBACK, memory)


def build_component(problem):
    return RuleMachine(problem, [BG()], Trans())
'''

# refine_rule que toca las transiciones: fuera de alcance
BG_TOUCHES_TRANSITION = BG_ONLY.replace('"name": "bg_only"', '"name": "bg_wider"').replace(
    'return ("bg", memory) if rules.applies("bg") else (FALLBACK, memory)',
    'return ("bg", memory) if rules.applies("bg") and rules.active != FALLBACK else (FALLBACK, memory)')
# refine_rule válido: solo cambia el desempate de la regla (primero el grupo más alto)
BG_REFINED = BG_ONLY.replace('"name": "bg_only"', '"name": "bg_high_first"').replace(
    "out.append((L.g(sd) - L.g(so), so, sd))", "out.append((L.g(sd) - L.g(so), -L.g(so), so, sd))").replace(
    "return [Move(so, sd) for _, so, sd in sorted(out)]", "return [Move(so, sd) for _, _, so, sd in sorted(out)]")


def _fenced(src):
    return f"```python\n{src}\n```"


def test_from_the_minimal_machine_the_schedule_adds_a_state_then_refines_it(tmp_path):
    # ronda 2: fuera de alcance, y el turno de corrección insiste → rechazo; ronda 3: refinamiento válido
    client = ScriptedClient(responses=[_fenced(BG_ONLY), _fenced(BG_TOUCHES_TRANSITION), _fenced(BG_TOUCHES_TRANSITION),
                                       _fenced(BG_REFINED)])
    res = evolve(client, PACK, PACK.make_spec(), tmp_path, Harness(PACK), rounds=3, archive_size=4, tune_samples=2,
                 n_train=2, n_test=3, size="4x4", verbose=False)
    ops = [(r.get("op"), r.get("target"), r.get("status")) for r in res.individuals]
    assert ops[0] == ("base", None, "base")
    assert ops[1][:2] == ("add_rule", None) and ops[1][2] == "archivo"
    assert ops[2] == ("refine_rule", "bg", "rechazado") and "transiciones" in res.individuals[2]["reason"]
    assert ops[3][:2] == ("refine_rule", "bg")
    base, bg = res.individuals[0], res.individuals[1]
    assert bg["fitness"] < base["fitness"]  # un estado BG ya mejora al comodín solo
    first, second, repair, third = (c[1] for c in client.calls)
    assert "`add_rule`" in first and "_default" in first and "comodín del framework" in first  # diagnóstico: todo es comodín
    assert "`refine_rule`" in second and "`bg`" in second
    assert "RECHAZADO" in repair and "transiciones" in repair and "class BG" in repair  # corrección dentro de la ronda
    assert res.individuals[2]["repaired"] is False
    assert "ya rechazados" in third and "transiciones" in third
    assert "bg_only" in res.archive


BG_AND_OTHER = BG_ONLY.replace("""class Trans:""", """class Other:
    name = "other"

    def propose(self, L, memory):
        return []


class Trans:""").replace("RuleMachine(problem, [BG()], Trans())", "RuleMachine(problem, [BG(), Other()], Trans())")


def test_scope_of_each_operator():
    """Reglas y transiciones son clases separadas: el alcance se verifica clase por clase."""
    parent = Individual(0, "bg_only", BG_ONLY, None, {}, ("bg",))
    assert scope_check("refine_rule", "bg", parent, ("bg",), BG_REFINED) is None
    assert "transiciones" in scope_check("refine_rule", "bg", parent, ("bg",), BG_TOUCHES_TRANSITION)
    assert "bg" in scope_check("change_transitions", None, parent, ("bg",), BG_REFINED)
    assert scope_check("change_transitions", None, parent, ("bg",), BG_TOUCHES_TRANSITION) is None
    assert "exactamente una regla" in scope_check("add_rule", None, parent, ("bg",), BG_ONLY)
    assert scope_check("add_rule", None, parent, ("bg", "other"), BG_AND_OTHER) is None
    changed = BG_AND_OTHER.replace("out.append((L.g(sd) - L.g(so), so, sd))", "out.append((L.g(so) - L.g(sd), so, sd))")
    assert "no cambia las reglas" in scope_check("add_rule", None, parent, ("bg", "other"), changed)
    assert "no agrega" in scope_check("simplify", None, parent, ("bg", "x"), BG_ONLY)


def test_the_archive_keeps_the_best_of_each_niche():
    def ind(i, n, f):
        return Individual(i, f"m{i}", "", None, {}, tuple(f"s{k}" for k in range(n)), fitness=f)

    archive = [ind(0, 1, 40.0)]
    assert admit(archive, ind(1, 1, 30.0), 3)
    assert admit(archive, ind(2, 2, 35.0), 3)  # peor que el mejor de 1 estado, pero es el único de 2: entra
    assert admit(archive, ind(3, 1, 20.0), 3)
    assert {x.id for x in archive} == {1, 2, 3}  # sale el peor del nicho repetido
    assert not admit(archive, ind(4, 1, 50.0), 3)
    assert not admit(archive, ind(5, 3, float("inf")), 3)


def test_tuning_in_the_loop_uses_the_declared_parameters(tmp_path):
    import importlib.util

    path = tmp_path / "m.py"
    path.write_text(MACHINE_MODULE)
    spec = importlib.util.spec_from_file_location("m_evolve", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sz = PACK.parse_size("4x4")
    train, test = PACK.make_instances(2, 1, sz), PACK.make_instances(2, 2, sz)
    h = Harness(PACK)
    params, tr, te = tune(h, mod.build_component, mod.COMPONENT, train, test, samples=5, rng=Random(0))
    assert set(params) == {"max_gap", "height_weight"}
    assert tr <= h.mean(mod.build_component, {"max_gap": 3, "height_weight": 1.0}, train)  # nunca peor que los defaults


def test_a_seed_and_the_minimal_machine_are_valid_starting_points(tmp_path):
    from llm.evolve import base_individual

    seed, is_seed = base_individual(PACK, tmp_path, "frg_machine", None)
    assert is_seed and seed.states == ("bg_move", "reduce_stack") and "from examples.cpmp.frg import" in seed.source
    minimal, is_seed = base_individual(PACK, tmp_path, None, None)
    assert not is_seed and minimal.source == MINIMAL and minimal.states == ()


def test_parents_come_from_every_niche():
    """Corrida 66: el nicho de dos estados sobrevivía en el archivo pero el torneo global nunca lo
    elegía. Ahora se elige primero el nicho y el de la máquina mínima solo si no hay otro."""
    from llm.evolve import select_parent

    def ind(i, n, f):
        return Individual(i, f"m{i}", "", None, {}, tuple(f"s{k}" for k in range(n)), fitness=f)

    archive = [ind(0, 0, 44.0), ind(1, 1, 29.0), ind(2, 1, 50.0), ind(3, 2, 56.0)]
    rng = Random(0)
    picked = [select_parent(archive, rng).id for _ in range(200)]
    assert 0 not in picked and 3 in picked and picked.count(3) > 40


def test_a_run_can_be_resumed_from_its_archive(tmp_path):
    first = ScriptedClient(responses=[_fenced(BG_ONLY)])
    evolve(first, PACK, PACK.make_spec(), tmp_path, Harness(PACK), rounds=1, tune_samples=2, n_train=2, n_test=3, size="4x4",
           verbose=False)
    assert (tmp_path / "evolve_archive.json").exists()
    second = ScriptedClient(responses=[_fenced(BG_REFINED)])
    res = evolve(second, PACK, PACK.make_spec(), tmp_path, Harness(PACK), rounds=1, tune_samples=2, n_train=2, n_test=3,
                 size="4x4", verbose=False, resume=True)
    retaken = [r["name"] for r in res.individuals if r.get("status") == "retomado"]
    assert set(retaken) == {"minimal", "bg_only"}
    assert "`bg`" in second.calls[0][1]  # el padre retomado sigue con su calendario (refinar bg)


def test_the_schedule_moves_on_after_two_failed_refinements():
    """Corrida 67: cinco refine_priority(finish) seguidos sin mejora. Tras dos, otro operador."""
    from llm.evolve import schedule

    parent = Individual(0, "m", "", None, {}, ("repair", "finish"), todo=["finish"])
    parent.profile = {"repair": {"steps": 5, "lost": 3.0, "rising": 2}, "finish": {"steps": 2, "lost": 1.0, "rising": 1}}
    assert schedule(parent, Random(0)) == ("refine_rule", "finish")
    parent.refine_failures["finish"] = 2
    ops = {schedule(parent, Random(s)) for s in range(30)}
    assert ("refine_rule", "finish") not in ops or len(ops) > 1
    assert any(op != "refine_rule" for op, _ in ops)


def test_infeasible_instances_cost_a_finite_penalty():
    class Stuck:  # nunca ordena: se queda sin candidatos y el respaldo decide
        states = ("x",)
        def initial(self, L): return "x", ()
        def transition(self, L, s, m): return "x", ()
        def score(self, L, s, m, a): return 0.0
        def update(self, L, s, m, a): return m

    h = Harness(PACK)
    inst = PACK.make_instances(1, 3, PACK.parse_size("4x4"))[0]
    v = h.run(lambda P, **k: Stuck(), {}, inst)
    assert v != float("inf") and v > 0


def test_mixed_sizes_and_the_self_sorted_line_reach_the_prompt(tmp_path):
    client = ScriptedClient(responses=[_fenced(BG_ONLY)])
    res = evolve(client, PACK, PACK.make_spec(), tmp_path, Harness(PACK), rounds=1, tune_samples=1, n_train=1, n_test=1,
                 size="4x4,5x5", verbose=False)
    assert res.individuals[1]["status"] == "archivo"
    client2 = ScriptedClient(responses=[_fenced(BG_REFINED)])
    evolve(client2, PACK, PACK.make_spec(), tmp_path, Harness(PACK), rounds=1, tune_samples=1, n_train=1, n_test=1,
           size="4x4,5x5", verbose=False, resume=True)
    prompt = client2.calls[0][1]
    assert "Completa sola" in prompt and "cvs_4x4" in prompt and "cvs_5x5" in prompt


def test_the_oracle_is_exact_and_regret_adds_up_to_the_gap():
    """Oráculo del CPMP (A*, h = mal puestos): coincide con el BFS de los casos; el arrepentimiento
    por paso de una máquina suma exactamente movimientos − óptimo."""
    from core.machine import MachinePolicy, machine_regret
    from examples.cpmp.cases import bfs_optimum
    from examples.cpmp.instance import CPMPInstance
    from examples.cpmp.machine import FRGMachine
    from examples.cpmp.oracle import optimal_distance, oracle_distance

    for k in range(4):
        inst = CPMPInstance.cvs_like(4, 4, Random(k))
        assert optimal_distance(tuple(tuple(s) for s in inst.stacks), inst.H) == len(bfs_optimum(inst))
    for inst in PACK.make_instances(3, 7, PACK.parse_size("4x4")):
        P = PACK.problem_factory(inst)
        r = machine_regret(MachinePolicy(FRGMachine(P), P), P.construction_view(inst), lambda p: oracle_distance(inst, p))
        moves = P.objective(GreedyConstructor(P, FRGMachine(P)).build(inst, Random(0)))
        opt = optimal_distance(tuple(tuple(s) for s in inst.stacks), inst.H)
        assert sum(row["regret"] for row in r["by_state"].values()) == moves - opt
        view = P.construction_view(inst)
        for e in r["examples"]:
            assert e["regret"] > 0 and e["chosen"] not in e["optimal"]
            assert len(e["optimal_scores"]) == len(e["optimal"]) and isinstance(e["chosen_score"], float)
            # la continuación es un camino óptimo: cada acción baja la distancia exactamente en 1
            q, d = e["partial"], oracle_distance(inst, e["partial"])
            for a in e["continuation"]:
                q = view.apply(q, a)
                assert oracle_distance(inst, q) == d - 1
                d -= 1
        for g in r["good"]:
            assert "chosen" in g and "state" in g
    big = PACK.make_instances(1, 7, PACK.parse_size("6x6"))[0]
    assert oracle_distance(big, PACK.problem_factory(big).construction_view(big).empty()) is None  # fuera de alcance, sin buscar


def test_counterexamples_reach_the_prompt(tmp_path):
    client = ScriptedClient(responses=[_fenced(BG_ONLY)])
    evolve(client, PACK, PACK.make_spec(), tmp_path, Harness(PACK), rounds=1, tune_samples=1, n_train=2, n_test=1,
           size="4x4", verbose=False)
    client2 = ScriptedClient(responses=[_fenced(BG_REFINED)])
    evolve(client2, PACK, PACK.make_spec(), tmp_path, Harness(PACK), rounds=1, tune_samples=1, n_train=2, n_test=1,
           size="4x4", verbose=False, resume=True)
    prompt = client2.calls[0][1]
    assert "Contra el óptimo" in prompt and "movimientos de más" in prompt
    assert "puntaje" in prompt and "TU score" in prompt  # por qué eligió la mala


BG_PLUS_BIG = BG_ONLY.replace('"name": "bg_only"', '"name": "bg_plus_big"').replace("""class Trans:""", """class Big:
    \"\"\"Solo en instancias de 5×5 o más: el tope de la pila más alta a la más baja.\"\"\"

    name = "big"

    def propose(self, L, memory):
        so = max(range(L.S), key=lambda s: (L.h(s), s))
        return [Move(so, sd) for sd in sorted(range(L.S), key=lambda s: (L.h(s), s)) if sd != so and L.e(sd) > 0]


class Trans:""").replace(
    'return ("bg", memory) if rules.applies("bg") else (FALLBACK, memory)',
    """if rules.applies("bg"):
            return "bg", memory
        if L.H >= 5 and L.S >= 5:
            return "big", memory
        return FALLBACK, memory""").replace("RuleMachine(problem, [BG()], Trans())", "RuleMachine(problem, [BG(), Big()], Trans())")


def test_a_state_for_larger_instances_is_reachable_through_the_training_set(tmp_path):
    """Corrida 68: estados que solo se activan con más contenedores se rechazaban porque las
    micro-instancias (4×4, 5×4) no los alcanzan. Con las de entrenamiento, se aceptan."""
    from llm.evolve import light_validation

    from core.validation.params import normalize_machine_file

    path = tmp_path / "big.py"
    path.write_text(BG_PLUS_BIG)
    contexts = PACK.make_contexts(strict=False)
    normalize_machine_file(path, [(c.instances[0], c.problem) for c in contexts])  # como en el loop: el 5 pasa a parámetro
    report, _, _ = light_validation(path, contexts)
    assert "states_reachable" in report.feedback()
    train = PACK.make_instances(2, 9100, PACK.parse_size("5x5"))
    report, _, _ = light_validation(path, contexts, [(i, PACK.problem_factory(i)) for i in train])
    assert report.passed, report.feedback()
