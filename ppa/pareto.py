"""Dominance stricte sur (énergie, temps, Area), tous à minimiser."""

from .model import Result


def dominates(a: Result, b: Result) -> bool:
    left = (a.energy_uj, a.time_us, a.area)
    right = (b.energy_uj, b.time_us, b.area)
    return all(x <= y for x, y in zip(left, right)) and any(x < y for x, y in zip(left, right))


def pareto_ks(results: list[Result]) -> set[int]:
    """Renvoie les k non dominés, indépendamment du seuil T_max."""
    return {candidate.k for candidate in results
            if not any(dominates(other, candidate) for other in results if other.k != candidate.k)}
