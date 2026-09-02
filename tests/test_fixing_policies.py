import pytest

from core.fixing_policies import SlidingWindowPolicy, consecutive_blocks, covers_all_variables

GROUPS = {f"t{t}": [f"y_{i}_{t}" for i in range(3)] for t in range(5)}
ALL = {v for vs in GROUPS.values() for v in vs}


def test_schedule_partitions_variables_in_every_step():
    for fix, integer, relax in SlidingWindowPolicy(2, 1).schedule(GROUPS):
        assert fix | integer | relax == ALL
        assert not (fix & integer) and not (fix & relax) and not (integer & relax)


def test_schedule_covers_all_variables_as_integer_at_least_once():
    for w, o in [(1, 0), (2, 0), (2, 1), (3, 2), (5, 0), (7, 0)]:
        assert covers_all_variables(SlidingWindowPolicy(w, o).schedule(GROUPS), ALL)


def test_first_window_fixes_nothing_and_last_relaxes_nothing():
    steps = list(SlidingWindowPolicy(2, 0).schedule(GROUPS))
    assert steps[0][0] == set()
    assert steps[-1][2] == set()


def test_overlap_reoptimizes_previous_group():
    steps = list(SlidingWindowPolicy(2, 1).schedule(GROUPS))
    # paso 1: ventana {t1, t2}; t1 vuelve a ser entero, solo t0 queda fijo
    assert steps[1][0] == set(GROUPS["t0"])
    assert set(GROUPS["t1"]) <= steps[1][1]


def test_blocks_partition_groups():
    blocks = consecutive_blocks(GROUPS, 2)
    assert len(blocks) == 3
    assert set().union(*blocks) == ALL


def test_invalid_parameters_rejected():
    with pytest.raises(ValueError):
        SlidingWindowPolicy(0, 0)
    with pytest.raises(ValueError):
        SlidingWindowPolicy(2, 2)
