import numpy as np
import pytest

from optimization.instance import build_instance
from optimization.stochastic import solve_stochastic_extensive_form


@pytest.fixture
def instance():
    return build_instance()


def test_stochastic_feasibility(instance):
    result = solve_stochastic_extensive_form(instance, integer_first_stage=True)
    x, y, z = result["x"], result["y"], result["z"]
    assert np.isclose(x.sum(), instance.budget)
    assert np.all(y >= -1e-9) and np.all(y <= instance.hedge_cap + 1e-9)
    assert np.all(z >= -1e-9)
    # restrição de recurso respeitada em cada cenário
    r = instance.scenario_returns(x)
    assert np.all(z >= instance.tau - r - y - 1e-6)


def test_relaxed_first_stage_is_lower_bound_for_integer_first_stage(instance):
    relaxed = solve_stochastic_extensive_form(instance, integer_first_stage=False)
    integer = solve_stochastic_extensive_form(instance, integer_first_stage=True)
    assert relaxed["objective"] <= integer["objective"] + 1e-6
