"""MILP (Mixed-Integer Linear Programming) — formulação real do problema.

Mesma formulação de ``optimization/lp.py``, mas com ``x_i`` binário (seleção
real de ativos, não fração). Resolvido com Pyomo + HiGHS (``appsi_highs``).

    min   -mu^T x + lam * sum_s p_s * y_s
    s.a.  sum_i x_i = budget
          y_s >= tau - scenarios[s] . x      para cada cenário s
          x_i in {0, 1}
          y_s >= 0
"""
from __future__ import annotations

import numpy as np
import pyomo.environ as pyo

from .instance import PortfolioInstance


def solve_milp(instance: PortfolioInstance, time_limit: float = 30.0) -> dict:
    n = instance.n_assets
    S = instance.n_scenarios

    m = pyo.ConcreteModel()
    m.I = pyo.RangeSet(0, n - 1)
    m.S = pyo.RangeSet(0, S - 1)
    m.x = pyo.Var(m.I, within=pyo.Binary)
    m.y = pyo.Var(m.S, within=pyo.NonNegativeReals)

    m.budget_con = pyo.Constraint(expr=sum(m.x[i] for i in m.I) == instance.budget)

    def shortfall_rule(model, s):
        r_s = sum(instance.scenarios[s][i] * model.x[i] for i in model.I)
        return model.y[s] >= instance.tau - r_s

    m.shortfall_con = pyo.Constraint(m.S, rule=shortfall_rule)

    m.obj = pyo.Objective(
        expr=-sum(instance.mu[i] * m.x[i] for i in m.I)
        + instance.lam * sum(instance.probabilities[s] * m.y[s] for s in m.S),
        sense=pyo.minimize,
    )

    solver = pyo.SolverFactory("appsi_highs")
    solver.options["time_limit"] = time_limit
    result = solver.solve(m, tee=False)

    x = np.array([pyo.value(m.x[i]) for i in range(n)])
    return {
        "x": x,
        "objective": float(pyo.value(m.obj)),
        "status": str(result.solver.termination_condition),
    }
