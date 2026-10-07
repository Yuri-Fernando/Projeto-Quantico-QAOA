"""Programação estocástica de 2 estágios com recurso, forma extensiva (monolítica).

Estágio 1 (aqui-e-agora): escolher quais ativos entram na carteira,
``x_i in {0,1}`` (ou relaxado em ``[0,1]`` quando ``integer_first_stage=False``
— usado para comparar com a decomposição de Benders, que opera sobre a
relaxação contínua do master problem).

Estágio 2 (recurso, por cenário ``s``, DEPOIS de observar o retorno
realizado): comprar um hedge ``y_s in [0, hedge_cap]`` a um custo
``hedge_cost`` por unidade, que reduz o shortfall residual ``z_s``:

    z_s >= tau - scenarios[s].x - y_s
    z_s >= 0

Objetivo (valor esperado):

    min   -mu^T x + lam * E_s[ z_s + hedge_cost * y_s ]
    s.a.  sum_i x_i = budget

Esta é a "forma extensiva" (deterministic equivalent) do programa
estocástico: resolve TODOS os cenários de uma vez, sem decomposição. Serve
de referência (ground truth) para validar a decomposição de Benders em
``optimization/benders.py``.
"""
from __future__ import annotations

import numpy as np
import pyomo.environ as pyo

from .instance import PortfolioInstance


def solve_stochastic_extensive_form(
    instance: PortfolioInstance,
    integer_first_stage: bool = True,
    time_limit: float = 30.0,
) -> dict:
    n = instance.n_assets
    S = instance.n_scenarios

    m = pyo.ConcreteModel()
    m.I = pyo.RangeSet(0, n - 1)
    m.S = pyo.RangeSet(0, S - 1)

    domain = pyo.Binary if integer_first_stage else pyo.UnitInterval
    m.x = pyo.Var(m.I, within=domain)
    m.y = pyo.Var(m.S, bounds=(0.0, instance.hedge_cap))
    m.z = pyo.Var(m.S, within=pyo.NonNegativeReals)

    m.budget_con = pyo.Constraint(expr=sum(m.x[i] for i in m.I) == instance.budget)

    def shortfall_rule(model, s):
        r_s = sum(instance.scenarios[s][i] * model.x[i] for i in model.I)
        return model.z[s] >= instance.tau - r_s - model.y[s]

    m.shortfall_con = pyo.Constraint(m.S, rule=shortfall_rule)

    m.obj = pyo.Objective(
        expr=-sum(instance.mu[i] * m.x[i] for i in m.I)
        + instance.lam
        * sum(instance.probabilities[s] * (m.z[s] + instance.hedge_cost * m.y[s]) for s in m.S),
        sense=pyo.minimize,
    )

    solver = pyo.SolverFactory("appsi_highs")
    solver.options["time_limit"] = time_limit
    result = solver.solve(m, tee=False)

    x = np.array([pyo.value(m.x[i]) for i in range(n)])
    y = np.array([pyo.value(m.y[s]) for s in range(S)])
    z = np.array([pyo.value(m.z[s]) for s in range(S)])
    return {
        "x": x,
        "y": y,
        "z": z,
        "objective": float(pyo.value(m.obj)),
        "status": str(result.solver.termination_condition),
    }
