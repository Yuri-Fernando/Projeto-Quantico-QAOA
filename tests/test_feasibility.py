"""T03 — nenhuma solução reportada como válida com sum(x) != k; gap relativo sem denominador degenerado."""
import numpy as np
import pytest

from optimization.canonical_qubo import CardinalityProblem
from optimization.classical_qubo import solve_enumeration
from optimization.instance import build_instance, generate_portfolio_instance
from quantum.measurement import analyze_counts
from quantum.runner import QAOAConfig, run_qaoa


@pytest.fixture
def problem():
    return build_instance().to_problem()  # n=3, k=2


def test_only_infeasible_samples_yield_no_solution(problem):
    f_star = solve_enumeration(problem)["objective"]
    out = analyze_counts(problem, {"000": 10, "111": 5, "001": 3}, f_star)
    assert out["status"] == "no_feasible_sample"
    assert out["solution"] is None and out["f_best"] is None
    assert out["feasible_rate"] == 0.0 and out["invalid_shot_rate"] == 1.0


def test_infeasible_low_energy_bitstring_is_never_reported(problem):
    exact = solve_enumeration(problem)
    # "001" (só x_0) tem f menor que qualquer viável? Não importa: é inviável e não pode ser reportado.
    out = analyze_counts(problem, {"001": 900, "110": 50, "011": 50}, exact["objective"])
    assert out["status"] == "feasible_found"
    assert sum(out["solution"]) == problem.k
    assert out["solution_bitstring"] in {"110", "011"}
    assert out["feasible_rate"] == pytest.approx(0.1)
    assert out["most_probable_is_feasible"] is False


def test_gap_relative_is_none_when_optimum_is_zero():
    zero = CardinalityProblem(name="z", domain="test", labels=("a", "b"), Q=np.zeros((2, 2)), constant=0.0, k=1)
    out = analyze_counts(zero, {"01": 4}, f_star=0.0)
    assert out["gap_abs"] == 0.0 and out["gap_rel"] is None


@pytest.mark.parametrize("mixer", ["x", "xy_ring"])
@pytest.mark.parametrize("penalty_factor", [0.05, 1.0])
def test_runner_reports_only_feasible_solutions(mixer, penalty_factor):
    problem = generate_portfolio_instance(6, seed=2).to_problem()
    rec = run_qaoa(problem, QAOAConfig(p=1, mixer=mixer, penalty_factor=penalty_factor, maxiter=40, seed=1,
                                       shots=256)).record
    if rec["status"] == "feasible_found":
        assert sum(rec["solution"]) == problem.k
        assert rec["f_best"] >= rec["f_star"] - 1e-12
    else:
        assert rec["solution"] is None
    if mixer == "xy_ring":
        assert rec["feasible_rate"] == 1.0
