"""El tuner por etapas: restringir el espacio a unas estructuras y volver de una configuración a los nodos."""

from config_space.space import ConfigSpace, build_config_space
from tuning.staged import restrict, unfold, write_configurations


def _space() -> ConfigSpace:
    from core.component import ComponentRegistry, ComponentSpec

    reg = ComponentRegistry()
    for name, params in (("a", {"x": {"type": "int", "range": [1, 5]}}), ("b", {"y": {"type": "float", "range": [0, 1]}})):
        reg.register(ComponentSpec(name, "neighborhood", ("SA", "ILS"), (), params, None))
    return build_config_space(reg, ["SA", "ILS"], {"SA": ["neighborhood"], "ILS": ["neighborhood"]},
                              {"SA": {"T0": {"type": "float", "range": [1, 9]}}, "ILS": {"k": {"type": "int", "range": [1, 3]}}})


def test_restrict_and_unfold(tmp_path):
    space = _space()
    small = restrict(space, {"skeleton": {"ILS"}, "neighborhood": {"a"}})
    names = [n.name for n in small.nodes]
    assert names == ["skeleton", "neighborhood", "a.x", "ILS.k"]
    cfg = {"skeleton": "ILS", "neighborhood": "a", "a.x": 3, "ILS.k": 2, "b.y": 0.5, "SA.T0": 2.0}
    assert unfold(small, cfg) == {"skeleton": "ILS", "neighborhood": "a", "a.x": 3, "ILS.k": 2}
    write_configurations(small, [cfg], tmp_path / "c.txt")
    assert (tmp_path / "c.txt").read_text().splitlines() == ["skeleton neighborhood a.x ILS.k", '"ILS" "a" 3 2']
