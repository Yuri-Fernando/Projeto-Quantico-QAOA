"""LP (Linear Programming) — relaxação linear do problema de portfólio.

Formulação (todas as variáveis contínuas, problema 100% linear):

    min   -mu^T x + lam * sum_s p_s * y_s
    s.a.  sum_i x_i = budget
          y_s >= tau - scenarios[s] . x      para cada cenário s
          0 <= x_i <= 1
          y_s >= 0

``y_s`` é a variável auxiliar padrão de linearização de ``max(0, ·)`` usada
para representar o shortfall esperado abaixo da meta ``tau`` como um
programa linear. Resolvido com ``scipy.optimize.linprog`` (método HiGHS).

Esta é a relaxação contínua do MILP em ``optimization/milp.py`` — mesmas
restrições, exceto a integralidade de ``x``. Por ser uma relaxação de um
problema de MINIMIZAÇÃO, seu valor ótimo é sempre um LIMITE INFERIOR válido
para o valor ótimo do MILP (ver teste em ``tests/test_lp.py``).
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import linprog

from .instance import PortfolioInstance


def solve_lp_relaxation(instance: PortfolioInstance) -> dict:
    n = instance.n_assets
    S = instance.n_scenarios
    n_vars = n + S

    c = np.zeros(n_vars)
    c[:n] = -instance.mu
    c[n:] = instance.lam * instance.probabilities

    # y_s >= tau - scenarios[s].x  <=>  -scenarios[s].x - y_s <= -tau
    A_ub = np.zeros((S, n_vars))
    b_ub = np.zeros(S)
    for s in range(S):
        A_ub[s, :n] = -instance.scenarios[s]
        A_ub[s, n + s] = -1.0
        b_ub[s] = -instance.tau

    A_eq = np.zeros((1, n_vars))
    A_eq[0, :n] = 1.0
    b_eq = [instance.budget]

    bounds = [(0.0, 1.0)] * n + [(0.0, None)] * S

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
    if not res.success:
        raise RuntimeError(f"LP falhou: {res.message}")

    x = res.x[:n]
    return {
        "x": x,
        "objective": float(res.fun),
        "status": res.message,
        "success": bool(res.success),
    }
