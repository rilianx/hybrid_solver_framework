"""Etapa `evolve` (`llm.evolve`): un algoritmo de optimización chico sobre máquinas de estados
constructivas. Operadores tipados con alcance verificado, calendario (agregar estado → refinar su
prioridad), tuning corto de los parámetros dentro del loop, diagnóstico por estado y archivo con
nichos por cantidad de estados."""

from __future__ import annotations

from random import Random

import pytest

from examples.cpmp.pack import PACK
from llm import ScriptedClient
from llm.evolve import MINIMAL, Harness, Individual, admit, evolve, scope_check, tune
from tests.test_machine import MACHINE_MODULE

BG_ONLY = '''
COMPONENT = {"name": "bg_only", "slot": "construction_machine", "compatible_skeletons": ["CONSTRUCT"], "requires": [],
             "params": {}}

from core.machine import FALLBACK


class BGOnly:
    """Un solo estado: mover un mal puesto a una pila ordenada de grupo mayor o igual (la menor
    diferencia de grupos primero); si no hay, el comodín."""

    states = ("bg",)

    def __init__(self, problem):
        self.problem = problem

    def _bg(self, L):
        out = {}
        for so in range(L.S):
            if L.stacks[so] and not L.is_sorted_stack(so):
                for sd in range(L.S):
                    if sd != so and L.e(sd) > 0 and L.is_sorted_stack(sd) and L.g(sd) >= L.g(so):
                        out[(so, sd)] = L.g(sd) - L.g(so)
        return out

    def initial(self, L):
        return "bg", ()

    def transition(self, L, state, memory):
        return ("bg", ()) if self._bg(L) else (FALLBACK, ())

    def score(self, L, state, memory, a):
        d = self._bg(L).get((a.so, a.sd))
        return 1e6 if d is None else float(d)

    def update(self, L, state, memory, a):
        return memory


def build_component(problem):
    return BGOnly(problem)
'''

# refine_priority que toca transition: fuera de alcance
BG_TOUCHES_TRANSITION = BG_ONLY.replace('"name": "bg_only"', '"name": "bg_wider"').replace(
    'return ("bg", ()) if self._bg(L) else (FALLBACK, ())', 'return ("bg", ()) if len(self._bg(L)) >= 1 else (FALLBACK, ())')
# refine_priority válido: solo cambia el desempate de score
BG_REFINED = BG_ONLY.replace('"name": "bg_only"', '"name": "bg_high_first"').replace(
    "return 1e6 if d is None else float(d)", "return 1e6 if d is None else float(d) - L.g(a.so) / 1000")


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
    assert ops[1][:2] == ("add_state", None) and ops[1][2] == "archivo"
    assert ops[2] == ("refine_priority", "bg", "rechazado") and "transition" in res.individuals[2]["reason"]
    assert ops[3][:2] == ("refine_priority", "bg")
    base, bg = res.individuals[0], res.individuals[1]
    assert bg["fitness"] < base["fitness"]  # un estado BG ya mejora al comodín solo
    first, second, repair, third = (c[1] for c in client.calls)
    assert "`add_state`" in first and "_default" in first and "comodín del framework" in first  # diagnóstico: todo es comodín
    assert "`refine_priority`" in second and "`bg`" in second
    assert "RECHAZADO" in repair and "transition" in repair and "class BGOnly" in repair  # corrección dentro de la ronda
    assert res.individuals[2]["repaired"] is False
    assert "ya rechazados" in third and "transition" in third
    assert "bg_only" in res.archive


def test_scope_of_each_operator():
    parent = Individual(0, "bg_only", BG_ONLY, None, {}, ("bg",))
    assert scope_check("refine_priority", "bg", parent, ("bg",), BG_REFINED) is None
    assert "transition" in scope_check("refine_priority", "bg", parent, ("bg",), BG_TOUCHES_TRANSITION)
    assert "score" in scope_check("change_transition", None, parent, ("bg",), BG_REFINED)
    assert scope_check("change_transition", None, parent, ("bg",), BG_TOUCHES_TRANSITION) is None
    assert "exactamente un estado" in scope_check("add_state", None, parent, ("bg",), BG_ONLY)
    assert scope_check("add_state", None, parent, ("bg", "reduce"), BG_ONLY) is None
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
    assert is_seed and seed.states == ("fill", "reduce") and "from examples.cpmp.frg import" in seed.source
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
    assert schedule(parent, Random(0)) == ("refine_priority", "finish")
    parent.refine_failures["finish"] = 2
    ops = {schedule(parent, Random(s)) for s in range(30)}
    assert ("refine_priority", "finish") not in ops or len(ops) > 1
    assert any(op != "refine_priority" for op, _ in ops)


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
