import pytest

from ppa.model import Parameters, evaluate, evaluate_all


def test_reference_values():
    p = Parameters()
    r1, r2, r4, r8, r16, r32 = evaluate_all(p)
    assert r1.cycles == 1024
    assert r1.time_us == pytest.approx(10.24)
    assert r4.time_us == pytest.approx(2.56)
    assert r1.power_mw == pytest.approx(48.5)
    assert r8.power_mw == pytest.approx(136)
    assert r8.energy_uj == pytest.approx(0.17408)
    assert [r.area for r in (r1, r2, r4, r8, r16, r32)] == [121, 144, 196, 324, 676, 1764]
    assert [r.feasible for r in (r1, r2, r4, r8, r16, r32)] == [False, False, True, True, True, True]


def test_units_and_custom_parameters():
    r = evaluate(4, Parameters(n=1200, frequency_mhz=200, t_max_us=2))
    assert r.cycles == 300
    assert r.time_us == pytest.approx(1.5)
    assert r.energy_uj == pytest.approx(r.power_mw * r.time_us / 1000)
    assert r.operations_per_joule == pytest.approx(r.performance_per_watt)


def test_invalid_parameters():
    with pytest.raises(ValueError):
        Parameters(ks=(1, 1))
    with pytest.raises(ValueError):
        Parameters(frequency_mhz=0)
