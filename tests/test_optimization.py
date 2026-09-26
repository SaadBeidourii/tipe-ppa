import pytest

from ppa.model import Parameters, evaluate, evaluate_all
from ppa.optimization import Weights, costs, energy_optimum, ppa_optimum, references
from ppa.sensitivity import power_quadratic_sweep, weight_map


def test_reference_optima():
    p = Parameters()
    results = evaluate_all(p)
    scores = costs(results, Weights(), "k=1", evaluate(1, p))
    assert energy_optimum(results).k == 8
    assert ppa_optimum(results, scores).k == 4
    assert scores[4] < scores[8]


def test_no_feasible_architecture():
    p = Parameters(t_max_us=0.1)
    results = evaluate_all(p)
    scores = costs(results, Weights(), "k=1", evaluate(1, p))
    assert energy_optimum(results) is None
    assert ppa_optimum(results, scores) is None


def test_normalization_and_weights():
    p = Parameters()
    results = evaluate_all(p)
    ref1 = evaluate(1, p)
    assert references(results, "k=1", ref1) == (ref1.energy_uj, ref1.time_us, ref1.area)
    assert references(results, "maximum", ref1)[1] == pytest.approx(10.24)
    assert references(results, "minimum", ref1)[1] == pytest.approx(0.32)
    with pytest.raises(ValueError):
        Weights(0.5, 0.5, 0.5)


def test_sensitivity_map_and_robustness():
    p = Parameters()
    results = evaluate_all(p)
    x, y, matrix = weight_map(results, "k=1", evaluate(1, p), steps=10)
    assert x == y
    assert matrix[5][3] == 4  # α=0.5, β=0.3, γ=0.2
    assert matrix[10][10] is None
    sweep = power_quadratic_sweep(p, steps=20)
    assert sweep[5] == (0.5, 8)
