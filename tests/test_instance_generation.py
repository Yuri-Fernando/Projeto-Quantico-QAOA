"""T16 — gerador reprodutível, Sigma PSD e rejeição de parâmetros inválidos."""
import dataclasses

import numpy as np
import pytest

from optimization.instance import build_instance, generate_portfolio_instance


@pytest.mark.parametrize("n", [3, 6, 8, 10, 12])
def test_generated_instances_are_valid_and_reproducible(n):
    a = generate_portfolio_instance(n, seed=11)
    b = generate_portfolio_instance(n, seed=11)
    assert a.n_assets == n and a.budget == n // 2
    assert np.array_equal(a.sigma, b.sigma) and np.array_equal(a.mu, b.mu)
    assert np.linalg.eigvalsh(a.sigma).min() > 0
    assert a.to_problem().instance_hash == b.to_problem().instance_hash
    assert a.to_problem().instance_hash != generate_portfolio_instance(n, seed=12).to_problem().instance_hash


def test_original_instance_still_builds():
    assert build_instance().n_assets == 3


@pytest.mark.parametrize(
    "change",
    [
        {"sigma": np.array([[0.04, 0.02, 0.0], [0.0, 0.035, 0.0], [0.0, 0.0, 0.03]])},  # assimétrica
        {"sigma": np.array([[1.0, 2.0, 0.0], [2.0, 1.0, 0.0], [0.0, 0.0, 1.0]])},  # não PSD
        {"budget": 4},
        {"budget": 0},
        {"lam": -1.0},
        {"mu": np.array([0.01, np.nan, 0.02])},
    ],
)
def test_invalid_parameters_are_rejected(change):
    with pytest.raises(ValueError):
        dataclasses.replace(build_instance(), **change)


def test_canonical_problem_rejects_lower_triangular_q():
    from optimization.canonical_qubo import CardinalityProblem

    with pytest.raises(ValueError):
        CardinalityProblem(name="x", domain="t", labels=("a", "b"), Q=np.array([[0.0, 0.0], [1.0, 0.0]]),
                           constant=0.0, k=1)
