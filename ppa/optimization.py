"""Choix contraint et coût PPA sans état d'interface."""

from dataclasses import dataclass

from .model import Result


NORMALIZATIONS = ("k=1", "maximum", "minimum")


@dataclass(frozen=True)
class Weights:
    alpha: float = 0.5
    beta: float = 0.3
    gamma: float = 0.2

    def __post_init__(self) -> None:
        if min(self.alpha, self.beta, self.gamma) < -1e-9:
            raise ValueError("Les poids doivent être positifs ou nuls.")
        if abs(self.alpha + self.beta + self.gamma - 1) > 1e-8:
            raise ValueError("La somme des poids doit être égale à 1.")


def references(results: list[Result], normalization: str, reference_k1: Result) -> tuple[float, float, float]:
    if not results:
        raise ValueError("La liste des configurations est vide.")
    if normalization == "k=1":
        chosen = (reference_k1.energy_uj, reference_k1.time_us, reference_k1.area)
    elif normalization in ("maximum", "minimum"):
        function = max if normalization == "maximum" else min
        chosen = tuple(function(getattr(r, field) for r in results)
                       for field in ("energy_uj", "time_us", "area"))
    else:
        raise ValueError("Normalisation inconnue.")
    if any(value <= 0 for value in chosen):
        raise ValueError("Les valeurs de référence doivent être strictement positives.")
    return chosen


def costs(results: list[Result], weights: Weights, normalization: str,
          reference_k1: Result) -> dict[int, float]:
    e_ref, t_ref, a_ref = references(results, normalization, reference_k1)
    return {r.k: weights.alpha * r.energy_uj / e_ref
            + weights.beta * r.time_us / t_ref
            + weights.gamma * r.area / a_ref for r in results}


def energy_optimum(results: list[Result]) -> Result | None:
    feasible = [r for r in results if r.feasible]
    return min(feasible, key=lambda r: (r.energy_uj, r.k)) if feasible else None


def ppa_optimum(results: list[Result], cost_by_k: dict[int, float]) -> Result | None:
    feasible = [r for r in results if r.feasible]
    return min(feasible, key=lambda r: (cost_by_k[r.k], r.k)) if feasible else None
