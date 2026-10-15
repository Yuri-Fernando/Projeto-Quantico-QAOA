"""Baselines clássicos EXATOS do mesmo objetivo resolvido pelo QAOA.

Diferente de ``milp.py``/``stochastic.py``/``benders.py`` (risco de *shortfall*, trilha de comparação
de MODELOS), tudo aqui resolve exatamente ``CardinalityProblem``:

    min  sum_i Q_ii x_i + sum_{i<j} Q_ij x_i x_j + c     s.a.  sum_i x_i = k,  x binário

- ``solve_enumeration``: oráculo combinatório (todas as ``C(n, k)`` seleções viáveis).
- ``solve_milp_linearized``: MILP com ``y_ij = x_i x_j`` linearizado por McCormick (exato para
  binários), resolvido por Pyomo + HiGHS. HiGHS não resolve MIQP, por isso a linearização.
- ``solve_milp_linearized(relax=True)``: relaxação LP do MESMO modelo — limite inferior válido (T18).
"""
from __future__ import annotations

import time
from itertools import combinations

import numpy as np
import pyomo.environ as pyo

from .canonical_qubo import CardinalityProblem

_TIE_TOL = 1e-12


def solve_enumeration(problem: CardinalityProblem, max_feasible: int = 2_000_000) -> dict:
    """Busca exaustiva vetorizada sobre as ``C(n, k)`` seleções viáveis (oráculo de referência)."""
    if problem.n_feasible > max_feasible:
        raise ValueError(f"C({problem.n},{problem.k})={problem.n_feasible} excede max_feasible={max_feasible}")
    t0 = time.perf_counter()
    combos = np.array(list(combinations(range(problem.n), problem.k)), dtype=np.int64)
    X = np.zeros((len(combos), problem.n))
    X[np.arange(len(combos))[:, None], combos] = 1.0
    values = problem.evaluate_many(X)
    best = int(np.argmin(values))
    f_star = float(values[best])
    scale = max(1.0, abs(f_star))
    optimal_mask = values <= f_star + _TIE_TOL * scale
    elapsed = time.perf_counter() - t0
    return {
        "method": "enumeration",
        "x": X[best],
        "objective": f_star,
        "status": "optimal",
        "certified": True,
        "n_feasible": int(len(values)),
        "n_optimal": int(optimal_mask.sum()),
        "optimal_indices": [int(sum(1 << i for i in c)) for c in combos[optimal_mask]],
        "f_worst_feasible": float(values.max()),
        "f_mean_feasible": float(values.mean()),
        "time_s": elapsed,
        "objective_id": problem.objective_id,
    }


def solve_milp_linearized(problem: CardinalityProblem, time_limit: float = 60.0, relax: bool = False) -> dict:
    """MILP com McCormick: ``y <= x_i``, ``y <= x_j``, ``y >= x_i + x_j - 1``, ``y >= 0``."""
    n = problem.n
    Q = problem.Q
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n) if Q[i, j] != 0.0]

    t0 = time.perf_counter()
    m = pyo.ConcreteModel()
    m.I = pyo.RangeSet(0, n - 1)
    m.P = pyo.Set(initialize=pairs, dimen=2)
    m.x = pyo.Var(m.I, within=pyo.UnitInterval if relax else pyo.Binary)
    m.y = pyo.Var(m.P, bounds=(0.0, 1.0))
    m.card = pyo.Constraint(expr=sum(m.x[i] for i in m.I) == problem.k)
    m.mc1 = pyo.Constraint(m.P, rule=lambda mm, i, j: mm.y[i, j] <= mm.x[i])
    m.mc2 = pyo.Constraint(m.P, rule=lambda mm, i, j: mm.y[i, j] <= mm.x[j])
    m.mc3 = pyo.Constraint(m.P, rule=lambda mm, i, j: mm.y[i, j] >= mm.x[i] + mm.x[j] - 1)
    m.obj = pyo.Objective(
        expr=sum(float(Q[i, i]) * m.x[i] for i in m.I)
        + sum(float(Q[i, j]) * m.y[i, j] for (i, j) in pairs)
        + problem.constant,
        sense=pyo.minimize,
    )
    t_build = time.perf_counter() - t0

    solver = pyo.SolverFactory("appsi_highs")
    solver.options["time_limit"] = time_limit
    t1 = time.perf_counter()
    result = solver.solve(m, tee=False)
    t_solve = time.perf_counter() - t1

    x = np.array([pyo.value(m.x[i]) for i in range(n)])
    status = str(result.solver.termination_condition)
    out = {
        "method": "lp_relaxation_mccormick" if relax else "milp_linearized",
        "x": x,
        "objective": float(pyo.value(m.obj)),
        "status": status,
        "certified": (status == "optimal") and not relax,
        "n_aux_vars": len(pairs),
        "n_constraints": 1 + 3 * len(pairs),
        "time_build_s": t_build,
        "time_solve_s": t_solve,
        "time_s": t_build + t_solve,
        "objective_id": problem.objective_id,
    }
    if not relax:
        x_bin = np.round(x)
        out["x"] = x_bin
        out["objective_recomputed"] = problem.evaluate(x_bin)
        out["feasible"] = problem.is_feasible(x_bin)
    return out
