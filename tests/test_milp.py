import numpy as np
import pytest

from optimization.instance import build_instance
from optimization.milp import solve_milp


@pytest.fixture
def instance():
    return build_instance()


def test_milp_solution_is_binary_and_respects_budget(instance):
    result = solve_milp(instance)
    x = result["x"]
    assert set(np.unique(np.round(x))).issubset({0.0, 1.0})
    assert np.isclose(x.sum(), instance.budget)
    assert result["status"] == "optimal"


def test_milp_objective_matches_independent_recomputation(instance):
    """O valor objetivo reportado pelo solver deve ser igual ao recomputado
    manualmente a partir do x retornado (confere que não há bug de sinal/escala)."""
    result = solve_milp(instance)
    x = result["x"]
    recomputed = -instance.mu @ x + instance.lam * (
        instance.probabilities @ np.maximum(0.0, instance.tau - instance.scenario_returns(x))
    )
    assert np.isclose(result["objective"], recomputed, atol=1e-6)
