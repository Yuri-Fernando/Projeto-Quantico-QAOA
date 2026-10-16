"""T02/T18 — baseline clássico do MESMO objetivo: MILP linearizado == enumeração; LP <= MILP."""
import numpy as np
import pytest

from optimization.classical_qubo import solve_enumeration, solve_milp_linearized
from optimization.heuristics import random_feasible_sampling, simulated_annealing
from optimization.instance import brute_force_optimum, build_instance, generate_portfolio_instance

CASES = [(n, s) for n in (3, 4, 6, 8) for s in (0, 1, 2)]


@pytest.mark.parametrize("n,seed", CASES)
def test_milp_linearized_matches_enumeration(n, seed):
    problem = generate_portfolio_instance(n, seed=seed).to_problem()
    exact = solve_enumeration(problem)
    milp = solve_milp_linearized(problem)
    assert milp["status"] == "optimal"
    assert milp["feasible"]
    assert milp["objective"] == pytest.approx(exact["objective"], abs=1e-7)
    assert milp["objective_recomputed"] == pytest.approx(exact["objective"], abs=1e-9)
    assert milp["objective_id"] == exact["objective_id"]


def test_enumeration_matches_legacy_brute_force_on_original_instance():
    instance = build_instance()
    bf_x, bf_val = brute_force_optimum(instance)
    exact = solve_enumeration(instance.to_problem())
    assert np.array_equal(exact["x"], bf_x)
    assert exact["objective"] == pytest.approx(bf_val, abs=1e-12)


@pytest.mark.parametrize("n,seed", [(4, 0), (6, 1), (8, 2)])
def test_lp_relaxation_of_same_objective_is_lower_bound(n, seed):
    problem = generate_portfolio_instance(n, seed=seed).to_problem()
    lp = solve_milp_linearized(problem, relax=True)
    milp = solve_milp_linearized(problem)
    assert lp["objective"] <= milp["objective"] + 1e-7


def test_heuristics_return_feasible_solutions_on_same_objective():
    problem = generate_portfolio_instance(8, seed=3).to_problem()
    f_star = solve_enumeration(problem)["objective"]
    sa = simulated_annealing(problem, seed=0)
    rnd = random_feasible_sampling(problem, n_samples=200, seed=0, f_star=f_star)
    for res in (sa, rnd):
        assert problem.is_feasible(res["x"])
        assert res["objective"] >= f_star - 1e-12
        assert res["objective"] == pytest.approx(problem.evaluate(res["x"]))
    assert 0.0 <= rnd["p_optimum"] <= 1.0
