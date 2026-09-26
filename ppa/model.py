"""Modèle idéal du produit scalaire et indices pédagogiques Power/Area.

Les puissances et surfaces calculées ici ne sont pas des mesures matérielles.
"""

from dataclasses import asdict, dataclass


DEFAULT_KS = (1, 2, 4, 8, 16, 32)


@dataclass(frozen=True)
class Parameters:
    n: int = 1024
    frequency_mhz: float = 100.0
    t_max_us: float = 3.0
    ks: tuple[int, ...] = DEFAULT_KS
    power_fixed_mw: float = 40.0
    power_linear_mw: float = 8.0
    power_quadratic_mw: float = 0.5
    area_fixed: float = 100.0
    area_linear: float = 20.0
    area_quadratic: float = 1.0

    def __post_init__(self) -> None:
        if self.n < 1 or self.frequency_mhz <= 0 or self.t_max_us <= 0:
            raise ValueError("N, f et T_max doivent être strictement positifs.")
        if not self.ks or any(k < 1 or k > self.n for k in self.ks):
            raise ValueError("Les valeurs de k doivent être comprises entre 1 et N.")
        if len(set(self.ks)) != len(self.ks):
            raise ValueError("Les valeurs de k doivent être distinctes.")
        coefficients = (
            self.power_fixed_mw, self.power_linear_mw, self.power_quadratic_mw,
            self.area_fixed, self.area_linear, self.area_quadratic,
        )
        if any(value < 0 for value in coefficients):
            raise ValueError("Les coefficients Power et Area doivent être positifs ou nuls.")
        if sum(coefficients[:3]) == 0 or sum(coefficients[3:]) == 0:
            raise ValueError("Power et Area doivent avoir au moins un coefficient positif.")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Result:
    k: int
    cycles: float
    time_us: float
    power_mw: float
    energy_uj: float
    area: float
    throughput_mops_s: float
    operations_per_joule: float
    performance_per_watt: float
    feasible: bool


def evaluate(k: int, p: Parameters) -> Result:
    """Évalue k selon l'hypothèse idéale N/k cycles, sans surcoût mémoire."""
    if k < 1 or k > p.n:
        raise ValueError("k doit être compris entre 1 et N.")
    cycles = p.n / k
    time_us = cycles / p.frequency_mhz  # cycles / MHz = microsecondes
    power_mw = p.power_fixed_mw + p.power_linear_mw * k + p.power_quadratic_mw * k**2
    area = p.area_fixed + p.area_linear * k + p.area_quadratic * k**2
    energy_uj = power_mw * time_us / 1000  # mW × µs = nJ
    throughput_mops_s = p.n / time_us  # opérations/µs = millions d'opérations/s
    operations_per_joule = p.n / (energy_uj * 1e-6)
    performance_per_watt = throughput_mops_s * 1e6 / (power_mw * 1e-3)
    return Result(k, cycles, time_us, power_mw, energy_uj, area,
                  throughput_mops_s, operations_per_joule, performance_per_watt,
                  time_us <= p.t_max_us + 1e-12)


def evaluate_all(p: Parameters) -> list[Result]:
    return [evaluate(k, p) for k in sorted(p.ks)]
