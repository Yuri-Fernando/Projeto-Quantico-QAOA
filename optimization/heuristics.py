"""Heurísticas clássicas no MESMO objetivo do QAOA (baselines de amostragem).

- ``random_feasible_sampling``: sorteia seleções viáveis uniformemente. É o baseline mínimo que um
  amostrador quântico precisa superar: se ``P(ótimo)`` do QAOA não passa de ``n_optimal / C(n,k)``,
  o circuito não está concentrando probabilidade em boas soluções.
- ``simulated_annealing``: movimentos de troca (sai um selecionado, entra um não selecionado), que
  preservam ``sum x = k`` — nenhuma solução inviável é visitada.
"""
from __future__ import annotations

import math
import time
from typing import Optional

import numpy as np

from .canonical_qubo import CardinalityProblem


def random_feasible_sampling(problem: CardinalityProblem, n_samples: int, seed: int,
                             f_star: Optional[float] = None) -> dict:
    rng = np.random.default_rng(seed)
    t0 = time.perf_counter()
    X = np.zeros((n_samples, problem.n))
    for s in range(n_samples):
        X[s, rng.choice(problem.n, size=problem.k, replace=False)] = 1.0
    values = problem.evaluate_many(X)
    best = int(np.argmin(values))
    out = {
        "method": "random_feasible_sampling",
        "x": X[best],
        "objective": float(values[best]),
        "f_mean": float(values.mean()),
        "evaluations": n_samples,
        "seed": seed,
        "time_s": time.perf_counter() - t0,
        "objective_id": problem.objective_id,
    }
    if f_star is not None:
        tol = 1e-9 * max(1.0, abs(f_star))
        out["p_optimum"] = float(np.mean(values <= f_star + tol))
    return out


def simulated_annealing(problem: CardinalityProblem, seed: int, n_steps: int = 2000,
                        t_start: Optional[float] = None, t_end: Optional[float] = None) -> dict:
    rng = np.random.default_rng(seed)
    t0 = time.perf_counter()
    n, k = problem.n, problem.k
    x = np.zeros(n)
    x[rng.choice(n, size=k, replace=False)] = 1.0
    f = problem.evaluate(x)
    scale = float(np.abs(problem.Q).max()) or 1.0
    t_start = scale if t_start is None else t_start
    t_end = scale * 1e-3 if t_end is None else t_end
    best_x, best_f = x.copy(), f
    evaluations = 1
    if 0 < k < n:
        for step in range(n_steps):
            temp = t_start * (t_end / t_start) ** (step / max(1, n_steps - 1))
            on = np.flatnonzero(x > 0.5)
            off = np.flatnonzero(x < 0.5)
            i, j = rng.choice(on), rng.choice(off)
            cand = x.copy()
            cand[i], cand[j] = 0.0, 1.0
            f_c = problem.evaluate(cand)
            evaluations += 1
            if f_c <= f or rng.random() < math.exp(-(f_c - f) / temp):
                x, f = cand, f_c
                if f < best_f:
                    best_x, best_f = x.copy(), f
    return {
        "method": "simulated_annealing",
        "x": best_x,
        "objective": float(best_f),
        "evaluations": evaluations,
        "seed": seed,
        "time_s": time.perf_counter() - t0,
        "objective_id": problem.objective_id,
    }
