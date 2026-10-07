"""Decomposição de Benders (L-shaped method) para o programa estocástico.

Implementação REAL do loop de cortes — não um wrapper que delega para um
solver que já faz decomposição internamente.

- **Master problem:** decide ``x in [0,1]^n`` (relaxação contínua, exigida
  pelo método clássico de Benders, cujos cortes de otimalidade pressupõem
  dualidade forte de um subproblema LINEAR contínuo) e uma variável
  ``eta`` que aproxima por baixo o custo de recurso esperado, sujeita aos
  cortes acumulados: ``eta >= alpha_k + beta_k . x``.
- **Subproblemas (um por cenário):** LP trivial de 2 variáveis
  (``y_s``, ``z_s``) resolvido via ``scipy.optimize.linprog``, do qual se
  extrai o valor ótimo e o multiplicador dual (sensibilidade do custo em
  relação ao RHS, que depende de ``x`` via ``scenarios[s] . x``) para
  construir o corte de otimalidade (subgradiente de uma função convexa
  linear por partes).

Converge para a MESMA solução que resolver a forma extensiva do
estocástico com ``integer_first_stage=False`` (ver
``optimization/stochastic.py``) — essa equivalência é testada em
``tests/test_benders.py``.
"""
from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pyomo.environ as pyo
from scipy.optimize import linprog

from .instance import PortfolioInstance


def _solve_scenario_subproblem(x: np.ndarray, instance: PortfolioInstance, s: int) -> Tuple[float, float]:
    """Resolve o subproblema de recurso do cenário s dado x fixo.

    min   hedge_cost * y_s + z_s
    s.a.  y_s + z_s >= tau - scenarios[s].x   (<=>  -y_s - z_s <= scenarios[s].x - tau)
          0 <= y_s <= hedge_cap
          z_s >= 0

    Retorna (valor_ótimo, dual) onde ``dual = d(valor_ótimo)/d(rhs)``.
    """
    r_s = float(instance.scenarios[s] @ x)
    b_ub = r_s - instance.tau

    c = [instance.hedge_cost, 1.0]  # [y_s, z_s]
    A_ub = [[-1.0, -1.0]]
    bounds = [(0.0, instance.hedge_cap), (0.0, None)]

    res = linprog(c, A_ub=A_ub, b_ub=[b_ub], bounds=bounds, method="highs")
    if not res.success:
        raise RuntimeError(f"Subproblema do cenário {s} falhou: {res.message}")

    dual = float(res.ineqlin.marginals[0])
    return float(res.fun), dual


def _solve_master(instance: PortfolioInstance, cuts: List[Tuple[float, np.ndarray]]):
    n = instance.n_assets
    m = pyo.ConcreteModel()
    m.I = pyo.RangeSet(0, n - 1)
    m.x = pyo.Var(m.I, bounds=(0.0, 1.0))
    m.eta = pyo.Var(bounds=(-1.0e6, None))
    m.budget_con = pyo.Constraint(expr=sum(m.x[i] for i in m.I) == instance.budget)

    m.cuts = pyo.ConstraintList()
    for alpha, beta in cuts:
        m.cuts.add(m.eta >= alpha + sum(float(beta[i]) * m.x[i] for i in m.I))

    m.obj = pyo.Objective(
        expr=-sum(instance.mu[i] * m.x[i] for i in m.I) + instance.lam * m.eta,
        sense=pyo.minimize,
    )
    pyo.SolverFactory("appsi_highs").solve(m, tee=False)

    x = np.array([pyo.value(m.x[i]) for i in range(n)])
    return x, float(pyo.value(m.obj)), float(pyo.value(m.eta))


def solve_benders(
    instance: PortfolioInstance,
    max_iter: int = 30,
    tol: float = 1e-6,
    verbose: bool = False,
) -> dict:
    n = instance.n_assets
    S = instance.n_scenarios
    cuts: List[Tuple[float, np.ndarray]] = []
    history = []

    best_x, best_obj = None, np.inf
    lb = -np.inf
    it = 0

    for it in range(1, max_iter + 1):
        x_curr, lb, eta_curr = _solve_master(instance, cuts)

        sub_vals = np.zeros(S)
        duals_scaled = np.zeros((S, n))  # duals_scaled[s] = dual_s * scenarios[s]
        for s in range(S):
            val, dual = _solve_scenario_subproblem(x_curr, instance, s)
            sub_vals[s] = val
            duals_scaled[s] = dual * instance.scenarios[s]

        recourse_cost = float(instance.probabilities @ sub_vals)
        ub_candidate = float(-instance.mu @ x_curr + instance.lam * recourse_cost)

        if ub_candidate < best_obj:
            best_obj, best_x = ub_candidate, x_curr.copy()

        # Corte de otimalidade: eta >= alpha + beta . x
        # f(x) ~= sum_s p_s*sub_vals[s] + sum_s p_s*dual_s*scenarios[s].(x - x_curr)
        alpha = float(instance.probabilities @ (sub_vals - duals_scaled @ x_curr))
        beta = instance.probabilities @ duals_scaled

        gap = ub_candidate - lb
        history.append(
            {"iter": it, "lower_bound": lb, "upper_bound": ub_candidate, "gap": gap, "x": x_curr.copy()}
        )
        if verbose:
            print(f"it={it:02d} lb={lb:.6f} ub={ub_candidate:.6f} gap={gap:.2e}")

        if gap < tol:
            break

        cuts.append((alpha, beta))

    return {
        "x": best_x,
        "objective": best_obj,
        "lower_bound": lb,
        "iterations": it,
        "converged": (best_obj - lb) < tol * 10,
        "history": history,
    }
