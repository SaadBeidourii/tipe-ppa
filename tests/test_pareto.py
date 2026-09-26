from ppa.model import Parameters, Result, evaluate_all
from ppa.pareto import dominates, pareto_ks


def make_result(k, e, t, a):
    return Result(k, 1, t, 1, e, a, 1, 1, 1, True)


def test_strict_dominance_and_equal_points():
    a = make_result(1, 1, 2, 3)
    b = make_result(2, 1, 2, 4)
    c = make_result(3, 1, 2, 3)
    assert dominates(a, b)
    assert not dominates(b, a)
    assert not dominates(a, c)
    assert pareto_ks([a, b, c]) == {1, 3}


def test_reference_frontier():
    results = evaluate_all(Parameters())
    assert pareto_ks(results) == {1, 2, 4, 8, 16, 32}


def test_dominated_architecture_with_constant_area():
    results = evaluate_all(Parameters(area_fixed=100, area_linear=0, area_quadratic=0))
    frontier = pareto_ks(results)
    assert 1 not in frontier  # k=2 est plus rapide, moins énergivore et a le même Area.
    assert 2 not in frontier
    assert 8 in frontier
