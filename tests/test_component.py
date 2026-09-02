from random import Random

import pytest

from core.component import ComponentRegistry, ComponentSpec, ComponentSpecError


def make_spec(**overrides):
    d = {
        "name": "two_opt_sampled",
        "slot": "neighborhood",
        "compatible_skeletons": ["HC", "SA"],
        "params": {
            "sample_size": {"type": "int", "range": [10, 500], "log": True},
            "strategy": {"type": "cat", "values": ["first", "best"]},
        },
    }
    d.update(overrides)
    return ComponentSpec.from_dict(d, impl=object())


def test_valid_component_spec_parses():
    spec = make_spec()
    assert spec.slot == "neighborhood"
    assert spec.is_compatible_with("SA")
    assert not spec.is_compatible_with("TS")


def test_unknown_slot_rejected():
    with pytest.raises(ComponentSpecError):
        make_spec(slot="not_a_slot")


def test_bad_range_rejected():
    with pytest.raises(ComponentSpecError):
        make_spec(params={"x": {"type": "int", "range": [10, 1]}})


def test_missing_values_for_cat_rejected():
    with pytest.raises(ComponentSpecError):
        make_spec(params={"x": {"type": "cat", "values": []}})


def test_empty_compatible_skeletons_means_universally_compatible():
    spec = make_spec(compatible_skeletons=[])
    assert spec.is_compatible_with("ANYTHING")


def test_registry_register_and_lookup():
    registry = ComponentRegistry()
    registry.register(make_spec())
    assert registry.get("neighborhood", "two_opt_sampled").name == "two_opt_sampled"
    assert registry.compatible("neighborhood", "SA")
    assert not registry.compatible("neighborhood", "TS")


def test_registry_rejects_duplicate_name_in_same_slot():
    registry = ComponentRegistry()
    registry.register(make_spec())
    with pytest.raises(ComponentSpecError):
        registry.register(make_spec())
