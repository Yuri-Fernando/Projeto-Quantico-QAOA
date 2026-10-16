import numpy as np
import pytest

from optimization.instance import brute_force_optimum, build_instance


@pytest.fixture
def instance():
    return build_instance()


def test_instance_has_expected_shape(instance):
    assert instance.n_assets == 3
    assert instance.budget == 2
    assert instance.scenarios.shape == (instance.n_scenarios, instance.n_assets)
    assert np.isclose(instance.probabilities.sum(), 1.0)


def test_feasible_selections_respect_budget(instance):
    for x in instance.feasible_selections():
        assert x.sum() == instance.budget
        assert set(np.unique(x)).issubset({0.0, 1.0})


def test_brute_force_finds_valid_feasible_optimum(instance):
    x, val = brute_force_optimum(instance)
    assert x.sum() == instance.budget
    assert np.isclose(val, instance.quadratic_objective(x))

    # Nenhuma seleção viável deve ter custo menor que o "ótimo" encontrado.
    for candidate in instance.feasible_selections():
        assert instance.quadratic_objective(candidate) >= val - 1e-9


def test_reproducible_scenarios_with_same_seed():
    inst1 = build_instance(seed=123)
    inst2 = build_instance(seed=123)
    assert np.allclose(inst1.scenarios, inst2.scenarios)
