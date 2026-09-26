"""Balayages de poids PPA et d'hypothèses de puissance."""

from dataclasses import replace

from .model import Parameters, Result, evaluate_all
from .optimization import Weights, costs, energy_optimum, ppa_optimum


def weight_map(results: list[Result], normalization: str, reference_k1: Result,
               steps: int = 40) -> tuple[list[float], list[float], list[list[int | None]]]:
    if steps < 1:
        raise ValueError("steps doit être positif.")
    grid = [i / steps for i in range(steps + 1)]
    matrix: list[list[int | None]] = []
    for alpha in grid:
        row = []
        for beta in grid:
            if alpha + beta > 1 + 1e-12:
                row.append(None)
                continue
            gamma = max(0.0, 1 - alpha - beta)
            c = costs(results, Weights(alpha, beta, gamma), normalization, reference_k1)
            optimum = ppa_optimum(results, c)
            row.append(optimum.k if optimum else None)
        matrix.append(row)
    return grid, grid, matrix


def power_quadratic_sweep(parameters: Parameters, steps: int = 80,
                          maximum: float = 2.0) -> list[tuple[float, int | None]]:
    if steps < 1 or maximum < 0:
        raise ValueError("Balayage invalide.")
    values = []
    for i in range(steps + 1):
        b = maximum * i / steps
        optimum = energy_optimum(evaluate_all(replace(parameters, power_quadratic_mw=b)))
        values.append((b, optimum.k if optimum else None))
    return values
