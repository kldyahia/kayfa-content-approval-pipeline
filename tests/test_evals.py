import pytest
from src.evals.metrics import (
    calculate_approval_within_n,
    calculate_average_revision_cycles,
    calculate_style_violation_catch_rate
)

def test_calculate_approval_within_n():
    results = [
        {"cycles": 2, "status": "approved"},
        {"cycles": 4, "status": "approved"},
        {"cycles": 1, "status": "rejected"}
    ]
    assert calculate_approval_within_n(results, n=3) == (1 / 3) * 100
    assert calculate_approval_within_n([]) == 0.0

def test_calculate_average_revision_cycles():
    results = [{"cycles": 2}, {"cycles": 4}]
    assert calculate_average_revision_cycles(results) == 3.0
    assert calculate_average_revision_cycles([]) == 0.0

def test_calculate_style_violation_catch_rate():
    results = [
        {"planted_violations": 2, "caught_violations": 1},
        {"planted_violations": 3, "caught_violations": 3}
    ]
    assert calculate_style_violation_catch_rate(results) == (4 / 5) * 100
    assert calculate_style_violation_catch_rate([]) == 0.0
    assert calculate_style_violation_catch_rate([{"planted_violations": 0, "caught_violations": 0}]) == 100.0