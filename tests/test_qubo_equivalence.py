"""T01 — paridade f original × QUBO × Ising × SparsePauliOp para todas as bitstrings (n <= 5)."""
import numpy as np
import pytest

from optimization.canonical_qubo import (
    basis_matrix,
    bitstring_to_x,
    critical_penalty,
    index_to_x,
    x_to_bitstring,
    x_to_index,
)
from optimization.instance import build_instance, generate_portfolio_instance
from optimization.qaoa import build_quadratic_program

TOL = 1e-9

INSTANCES = [build_instance()] + [
    generate_portfolio_instance(n, seed=s) for n in (3, 4, 5) for s in (0, 1)
]


@pytest.fixture(params=range(len(INSTANCES)), ids=lambda i: f"inst{i}")
def instance(request):
    return INSTANCES[request.param]


def test_problem_matches_original_objective_on_all_bitstrings(instance):
    problem = instance.to_problem()
    for x in basis_matrix(problem.n).astype(float):
        assert abs(problem.evaluate(x) - instance.quadratic_objective(x)) < TOL


@pytest.mark.parametrize("rho_factor", [0.0, 0.3, 1.0, 5.0])
def test_qubo_equals_objective_plus_penalty(instance, rho_factor):
    problem = instance.to_problem()
    rho = rho_factor * problem.safe_penalty()
    qubo = problem.penalized_qubo(rho)
    energies = qubo.energies()
    for b, x in enumerate(basis_matrix(problem.n).astype(float)):
        expected = problem.evaluate(x) + rho * (x.sum() - problem.k) ** 2
        assert abs(qubo.evaluate(x) - expected) < TOL
        assert abs(energies[b] - expected) < TOL


def test_ising_energy_and_pauli_operator_match_qubo_including_offset(instance):
    qubo = instance.to_problem().penalized_qubo()
    ising = qubo.to_ising()
    assert np.allclose(ising.energies(), qubo.energies(), atol=TOL)
    for b in range(2**qubo.n):
        z = 1.0 - 2.0 * index_to_x(b, qubo.n)
        assert abs(ising.energy_z(z) - qubo.energies()[b]) < TOL
    diag = np.real(np.diag(ising.to_sparse_pauli_op().to_matrix()))
    assert np.allclose(diag, qubo.energies(), atol=TOL)


def test_qubo_matches_qiskit_optimization_converter_with_same_penalty(instance):
    """Nosso QUBO == ``QuadraticProgramToQubo`` do qiskit-optimization para o mesmo rho."""
    from qiskit_optimization.converters import QuadraticProgramToQubo

    problem = instance.to_problem()
    rho = problem.safe_penalty()
    qiskit_qubo = QuadraticProgramToQubo(penalty=rho).convert(build_quadratic_program(instance))
    ours = problem.penalized_qubo(rho)
    for x in basis_matrix(problem.n).astype(float):
        assert abs(qiskit_qubo.objective.evaluate(x) - ours.evaluate(x)) < TOL


def test_bitstring_mapping_is_little_endian_and_roundtrips():
    x = np.array([1.0, 0.0, 0.0, 1.0, 1.0])
    assert x_to_bitstring(x) == "11001"  # qubit 0 é o caractere mais à direita
    assert np.array_equal(bitstring_to_x("11001"), x)
    assert x_to_index(x) == 0b11001
    assert np.array_equal(index_to_x(0b11001, 5), x)


def test_safe_penalty_makes_ground_state_feasible_and_optimal(instance):
    problem = instance.to_problem()
    energies = problem.penalized_qubo().energies()
    ground = index_to_x(int(np.argmin(energies)), problem.n)
    feasible_values = [problem.evaluate(x) for x in problem.feasible_selections()]
    assert problem.is_feasible(ground)
    assert abs(problem.evaluate(ground) - min(feasible_values)) < TOL
    assert critical_penalty(problem) <= problem.safe_penalty()


def test_penalty_below_critical_value_yields_infeasible_ground_state():
    """Penalidade baixa demais favorece solução inviável (risco descrito em P0.5)."""
    problem = build_instance().to_problem()
    rho_c = critical_penalty(problem)
    assert rho_c > 0
    ground = index_to_x(int(np.argmin(problem.penalized_qubo(0.5 * rho_c).energies())), problem.n)
    assert not problem.is_feasible(ground)
