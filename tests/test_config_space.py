from random import Random

from config_space import build_config_space, suggest_from_space, to_irace_parameters
from core.component import ComponentRegistry, ComponentSpec


def _toy_registry() -> ComponentRegistry:
    registry = ComponentRegistry()
    registry.register(
        ComponentSpec.from_dict(
            {
                "name": "greedy",
                "slot": "constructor",
                "compatible_skeletons": ["SA", "ILS"],
                "params": {},
            },
            impl=object(),
        )
    )
    registry.register(
        ComponentSpec.from_dict(
            {
                "name": "two_opt",
                "slot": "neighborhood",
                "compatible_skeletons": ["SA"],
                "params": {"sample_size": {"type": "int", "range": [10, 500], "log": True}},
            },
            impl=object(),
        )
    )
    registry.register(
        ComponentSpec.from_dict(
            {
                "name": "or_opt",
                "slot": "neighborhood",
                "compatible_skeletons": ["SA"],
                "params": {"segment_len": {"type": "cat", "values": [1, 2, 3]}},
            },
            impl=object(),
        )
    )
    return registry


def _toy_space():
    registry = _toy_registry()
    return build_config_space(
        registry,
        skeleton_names=["SA", "ILS"],
        slots_per_skeleton={"SA": ["constructor", "neighborhood"], "ILS": ["constructor"]},
        skeleton_params={"SA": {"T0": {"type": "float", "range": [0.1, 100], "log": True}}},
    )


def test_root_skeleton_param_has_no_condition():
    space = _toy_space()
    root = next(n for n in space.nodes if n.name == "skeleton")
    assert root.conditions == ()
    assert set(root.values) == {"SA", "ILS"}


def test_slot_param_conditioned_on_skeletons_that_use_it():
    space = _toy_space()
    neighborhood = next(n for n in space.nodes if n.name == "neighborhood")
    assert len(neighborhood.conditions) == 1
    cond = neighborhood.conditions[0]
    assert cond.parent == "skeleton" and cond.kind == "in" and cond.values == ("SA",)
    assert set(neighborhood.values) == {"two_opt", "or_opt"}


def test_component_param_conditioned_on_slot_choice():
    space = _toy_space()
    node = next(n for n in space.nodes if n.name == "two_opt.sample_size")
    assert len(node.conditions) == 2
    parents = {c.parent for c in node.conditions}
    assert parents == {"skeleton", "neighborhood"}


def test_irace_export_contains_conditions_and_log_comment():
    text = to_irace_parameters(_toy_space())
    assert 'skeleton "--skeleton=" c ("SA", "ILS")' in text
    assert "two_opt.sample_size" in text
    assert "log-scale" in text
    assert '| skeleton %in% c("SA")' in text


class _RecordingTrial:
    def __init__(self, rng: Random):
        self.rng = rng

    def suggest_int(self, name, low, high, *, log=False):
        return self.rng.randint(low, high)

    def suggest_float(self, name, low, high, *, log=False):
        return self.rng.uniform(low, high)

    def suggest_categorical(self, name, choices):
        return self.rng.choice(choices)


def test_optuna_suggest_only_activates_relevant_branch():
    space = _toy_space()
    rng = Random(0)
    # Forzamos ILS fijando la primera categórica que muestreará el "trial":
    # como el trial es determinístico dado el rng, comprobamos ambas ramas
    # posibles corriendo varias semillas.
    saw_sa, saw_ils = False, False
    for seed in range(30):
        trial = _RecordingTrial(Random(seed))
        assignment = suggest_from_space(space, trial)
        assert "skeleton" in assignment
        if assignment["skeleton"] == "SA":
            saw_sa = True
            assert "neighborhood" in assignment
            assert "T0" not in assignment or "SA.T0" in assignment
        elif assignment["skeleton"] == "ILS":
            saw_ils = True
            assert "neighborhood" not in assignment
    assert saw_sa and saw_ils


def test_optuna_suggest_never_activates_param_of_inactive_branch():
    space = _toy_space()
    for seed in range(30):
        trial = _RecordingTrial(Random(seed))
        assignment = suggest_from_space(space, trial)
        if assignment["skeleton"] == "ILS":
            assert not any(k.startswith("two_opt") or k.startswith("or_opt") for k in assignment)
            assert "SA.T0" not in assignment


def test_slot_is_split_by_skeleton_group_when_compatibility_differs():
    """La validación por combinación poda `compatible_skeletons` por componente. Con un solo
    parámetro `neighborhood` para SA e ILS, el tuner podía elegir un vecindario que ILS no
    admite (runs 9–14: trials perdidos por AssemblyError)."""
    from examples.lotsizing.random_search import RandomTrial
    from tuning.irace_scenario import parse_irace_params

    registry = _toy_registry()
    registry.register(ComponentSpec.from_dict(
        {"name": "swap", "slot": "neighborhood", "compatible_skeletons": ["SA", "ILS"],
         "params": {"k": {"type": "int", "range": [1, 3]}}}, impl=object()))
    space = build_config_space(
        registry, skeleton_names=["SA", "ILS"],
        slots_per_skeleton={"SA": ["constructor", "neighborhood"], "ILS": ["constructor", "neighborhood"]},
    )
    nodes = {n.name: n for n in space.nodes if n.config_key == "neighborhood"}
    assert set(nodes) == {"neighborhood__SA", "neighborhood__ILS"}
    assert set(nodes["neighborhood__ILS"].values) == {"swap"}
    allowed = {"SA": {"two_opt", "or_opt", "swap"}, "ILS": {"swap"}}
    for seed in range(200):
        config = suggest_from_space(space, RandomTrial(Random(seed)))
        assert config["neighborhood"] in allowed[config["skeleton"]]
        assert not any("__" in k for k in config)  # plegado a las claves del ensamblador
        if config["neighborhood"] == "swap":
            assert config["swap.k"] in (1, 2, 3)
    text = to_irace_parameters(space)
    assert "neighborhood__ILS" in text and 'skeleton %in% c("ILS")' in text
    assert parse_irace_params(space, ["--skeleton=ILS", "--neighborhood__ILS=swap", "--swap.k__ILS=2"]) == \
        {"skeleton": "ILS", "neighborhood": "swap", "swap.k": 2}
