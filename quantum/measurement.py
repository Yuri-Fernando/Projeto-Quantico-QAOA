"""Análise de amostras do QAOA: viabilidade, P(ótimo), melhor solução viável, gaps e ICs.

Regra central (auditoria P0.4): a solução reportada é SEMPRE a melhor bitstring VIÁVEL amostrada,
avaliada pela função original ``f``. Se nenhuma amostra satisfaz ``sum x = k``, a solução é ``None`` e
o status é ``"no_feasible_sample"`` — o ``status`` de um solver nunca substitui essa checagem.

Métricas sem denominadores artificiais: ``gap_rel`` só existe se ``|f*| > 1e-12``.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from math import sqrt
from typing import Optional

import numpy as np

from optimization.canonical_qubo import CardinalityProblem, basis_matrix, bitstring_to_x, x_to_bitstring

_REL_EPS = 1e-12


def _opt_tol(f_star: float) -> float:
    return 1e-9 * max(1.0, abs(f_star))


def analyze_counts(problem: CardinalityProblem, counts: Mapping[str, int], f_star: float,
                   qubo_energy: Optional[Callable[[np.ndarray], float]] = None) -> dict:
    """Métricas a partir de contagens (amostragem finita)."""
    shots = int(sum(counts.values()))
    if shots <= 0:
        raise ValueError("contagens vazias")
    if any(c < 0 for c in counts.values()):
        raise ValueError("contagem negativa")
    tol = _opt_tol(f_star)
    feasible_shots = optimal_shots = 0
    violations: dict[int, int] = {}
    f_feasible_weighted = 0.0
    energy_weighted = 0.0
    best_x, best_f = None, np.inf
    for key, c in counts.items():
        x = bitstring_to_x(key)
        if len(x) != problem.n:
            raise ValueError(f"bitstring {key!r} incompatível com n={problem.n}")
        d = int(round(x.sum())) - problem.k
        violations[d] = violations.get(d, 0) + c
        if qubo_energy is not None:
            energy_weighted += c * qubo_energy(x)
        if d != 0:
            continue
        f = problem.evaluate(x)
        feasible_shots += c
        f_feasible_weighted += c * f
        if f <= f_star + tol:
            optimal_shots += c
        if f < best_f:
            best_x, best_f = x, f
    most_probable = max(counts.items(), key=lambda kv: kv[1])[0]
    out = {
        "shots": shots,
        "n_distinct_bitstrings": len(counts),
        "feasible_shots": feasible_shots,
        "feasible_rate": feasible_shots / shots,
        "invalid_shot_rate": 1.0 - feasible_shots / shots,
        "optimal_shots": optimal_shots,
        "p_optimum": optimal_shots / shots,
        "p_optimum_ci95": wilson_interval(optimal_shots, shots),
        "cardinality_violation_hist": {str(k): v for k, v in sorted(violations.items())},
        "most_probable_bitstring": most_probable,
        "most_probable_is_feasible": problem.is_feasible(bitstring_to_x(most_probable)),
        "energy_mean": energy_weighted / shots if qubo_energy is not None else None,
        "f_mean_feasible": f_feasible_weighted / feasible_shots if feasible_shots else None,
        "f_star": f_star,
    }
    out.update(_solution_fields(problem, best_x, best_f, f_star))
    return out


def analyze_probabilities(problem: CardinalityProblem, probabilities: np.ndarray, f_star: float,
                          energies: Optional[np.ndarray] = None) -> dict:
    """Métricas EXATAS a partir das probabilidades da evolução ideal (sem amostragem)."""
    probabilities = np.asarray(probabilities, dtype=float)
    if np.any(probabilities < -1e-15):
        raise ValueError("probabilidade negativa")
    X = basis_matrix(problem.n).astype(float)
    feasible = X.sum(axis=1) == problem.k
    f = problem.evaluate_many(X)
    optimal = feasible & (f <= f_star + _opt_tol(f_star))
    p_feas = float(probabilities[feasible].sum())
    return {
        "p_feasible_exact": p_feas,
        "p_optimum_exact": float(probabilities[optimal].sum()),
        "expected_energy_exact": float(probabilities @ energies) if energies is not None else None,
        "expected_f_given_feasible_exact": (float(probabilities[feasible] @ f[feasible] / p_feas)
                                            if p_feas > 0 else None),
        "most_probable_bitstring_exact": x_to_bitstring(X[int(np.argmax(probabilities))]),
    }


def _solution_fields(problem: CardinalityProblem, best_x, best_f: float, f_star: float) -> dict:
    if best_x is None:
        return {"status": "no_feasible_sample", "solution": None, "solution_bitstring": None,
                "solution_labels": None, "f_best": None, "gap_abs": None, "gap_rel": None,
                "is_optimal": False}
    assert problem.is_feasible(best_x)
    gap = float(best_f - f_star)
    return {
        "status": "feasible_found",
        "solution": best_x.tolist(),
        "solution_bitstring": x_to_bitstring(best_x),
        "solution_labels": [lbl for lbl, xi in zip(problem.labels, best_x) if xi > 0.5],
        "f_best": float(best_f),
        "gap_abs": gap,
        "gap_rel": gap / abs(f_star) if abs(f_star) > _REL_EPS else None,
        "is_optimal": gap <= _opt_tol(f_star),
    }


# --------------------------------------------------------------------------- estatística
def wilson_interval(successes: int, n: int, z: float = 1.959964) -> list:
    """IC de Wilson para proporção binomial (melhor que Wald perto de 0 e 1)."""
    if n <= 0:
        return [None, None]
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = z * sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / denom
    return [max(0.0, center - half), min(1.0, center + half)]


def bootstrap_ci(values: Sequence[float], stat: Callable = np.mean, n_boot: int = 2000,
                 alpha: float = 0.05, seed: int = 0) -> list:
    """IC percentil por bootstrap (reamostragem das seeds/execuções independentes)."""
    arr = np.asarray([v for v in values if v is not None], dtype=float)
    if arr.size == 0:
        return [None, None]
    if arr.size == 1:
        return [float(arr[0]), float(arr[0])]
    rng = np.random.default_rng(seed)
    boots = np.array([stat(rng.choice(arr, size=arr.size, replace=True)) for _ in range(n_boot)])
    return [float(np.quantile(boots, alpha / 2)), float(np.quantile(boots, 1 - alpha / 2))]
