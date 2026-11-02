import pytest

from app.services.graph import find_shortest_path
from tests.conftest import SAMPLE_EDGES


def test_picks_cheaper_of_two_paths():
    total, path = find_shortest_path(SAMPLE_EDGES, "A", "D")
    assert total == pytest.approx(23.4)
    assert path == ["A", "B", "D"]


def test_two_hop_path_beats_expensive_direct_edge():
    edges = [("A", "B", 1), ("B", "C", 1), ("A", "C", 10)]
    assert find_shortest_path(edges, "A", "C") == (2, ["A", "B", "C"])


def test_unreachable_returns_none():
    edges = [("A", "B", 1), ("C", "D", 1)]
    assert find_shortest_path(edges, "A", "D") is None


def test_unknown_source_returns_none():
    assert find_shortest_path([("A", "B", 1)], "X", "B") is None


def test_source_equals_destination():
    assert find_shortest_path(SAMPLE_EDGES, "A", "A") == (0.0, ["A"])


def test_cycle_terminates():
    edges = [("A", "B", 1), ("B", "C", 1), ("C", "A", 1), ("C", "D", 5)]
    assert find_shortest_path(edges, "A", "D") == (7, ["A", "B", "C", "D"])


def test_cycle_without_destination_terminates():
    edges = [("A", "B", 1), ("B", "A", 1)]
    assert find_shortest_path(edges, "A", "Z") is None


def test_direction_matters():
    edges = [("A", "B", 1)]
    assert find_shortest_path(edges, "A", "B") == (1, ["A", "B"])
    assert find_shortest_path(edges, "B", "A") is None
