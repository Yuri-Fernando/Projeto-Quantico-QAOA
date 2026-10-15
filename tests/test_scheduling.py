"""E7 — segundo domínio com a MESMA família canônica; clássico e QAOA no mesmo objetivo."""
import numpy as np
import pytest

from optimization.canonical_qubo import basis_matrix
from optimization.classical_qubo import solve_enumeration, solve_milp_linearized
from optimization.scheduling import generate_shift_scheduling_instance
from quantum.runner import QAOAConfig, run_qaoa


@pytest.mark.parametrize("n,seed", [(4, 0), (6, 1), (8, 2), (10, 3)])
def test_scheduling_problem_objective_and_milp_parity(n, seed):
    inst = generate_shift_scheduling_instance(n, seed=seed)
    problem = inst.to_problem()
    S = inst.shared_resources
    for x in basis_matrix(n).astype(float)[:: max(1, 2**n // 64)]:
        manual = -inst.priority @ x + sum(inst.alpha * S[i, j] * x[i] * x[j]
                                          for i in range(n) for j in range(i + 1, n))
        assert problem.evaluate(x) == pytest.approx(manual, abs=1e-12)
    exact = solve_enumeration(problem)
    milp = solve_milp_linearized(problem)
    assert milp["objective"] == pytest.approx(exact["objective"], abs=1e-7)
    assert problem.domain == "shift_scheduling" and problem.objective_id == exact["objective_id"]


def test_conflict_graph_is_sparser_than_portfolio_covariance():
    from optimization.instance import generate_portfolio_instance

    sched = generate_shift_scheduling_instance(10, seed=0).to_problem()
    port = generate_portfolio_instance(10, seed=0).to_problem()
    nz = lambda p: np.count_nonzero(np.triu(p.Q, 1))  # noqa: E731
    assert nz(sched) < nz(port) == 45


def test_generator_is_reproducible():
    a = generate_shift_scheduling_instance(8, seed=5).to_problem()
    b = generate_shift_scheduling_instance(8, seed=5).to_problem()
    assert a.instance_hash == b.instance_hash


def test_qaoa_on_scheduling_reports_feasible_solution():
    problem = generate_shift_scheduling_instance(6, seed=1).to_problem()
    rec = run_qaoa(problem, QAOAConfig(p=2, mixer="xy_ring", maxiter=60, seed=0)).record
    assert rec["feasible_rate"] == 1.0
    assert sum(rec["solution"]) == problem.k
