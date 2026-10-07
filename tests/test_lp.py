import numpy as np
import pytest

from optimization.instance import build_instance
from optimization.lp import solve_lp_relaxation
from optimization.milp import solve_milp


@pytest.fixture
def instance():
    return build_instance()


def test_lp_relaxation_is_feasible(instance):
    result = solve_lp_relaxation(instance)
    assert result["success"]
    x = result["x"]
    assert np.isclose(x.sum(), instance.budget)
    assert np.all(x >= -1e-9)
    assert np.all(x <= 1 + 1e-9)


def test_lp_relaxation_is_lower_bound_for_milp(instance):
    """A relaxação contínua de um problema de MINIMIZAÇÃO nunca pode ter
    valor ótimo maior que o problema inteiro (feasible set maior)."""
    lp = solve_lp_relaxation(instance)
    milp = solve_milp(instance)
    assert lp["objective"] <= milp["objective"] + 1e-6
