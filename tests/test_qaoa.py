import numpy as np
import pytest

from optimization.instance import build_instance, brute_force_optimum
from optimization.qaoa import build_quadratic_program, solve_with_qaoa


@pytest.fixture
def instance():
    return build_instance()


def test_quadratic_program_matches_instance_objective(instance):
    """O QuadraticProgram construído para o QAOA deve avaliar, para toda
    seleção viável, exatamente o mesmo valor que ``instance.quadratic_objective``
    — garante que não há erro de sinal/escala na tradução para QUBO."""
    qp = build_quadratic_program(instance)
    for x in instance.feasible_selections():
        var_dict = {t: xi for t, xi in zip(instance.tickers, x)}
        qp_value = qp.objective.evaluate(var_dict)
        assert np.isclose(qp_value, instance.quadratic_objective(x))


def test_qaoa_finds_same_optimum_as_brute_force(instance):
    """No espaço pequeno desta instância (3 qubits), o QAOA com reps/otimizador
    suficientes deve encontrar exatamente a mesma solução da busca exaustiva."""
    bf_x, bf_val = brute_force_optimum(instance)

    result = solve_with_qaoa(instance, reps=3, maxiter=250, seed=42)

    assert np.array_equal(result["x"], bf_x)
    assert np.isclose(result["objective"], bf_val, atol=1e-6)
