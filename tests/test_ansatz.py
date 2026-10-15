"""Paridade circuito Qiskit × simulador exato; Dicke exato; mixer XY preserva cardinalidade."""
from math import comb

import numpy as np
import pytest
from qiskit.quantum_info import Statevector

from optimization.canonical_qubo import basis_matrix
from optimization.instance import generate_portfolio_instance
from quantum.ansatz import bind, build_qaoa_circuit, dicke_state_circuit
from quantum.simulator import ExactQAOASimulator, sample_counts


@pytest.mark.parametrize("n,k", [(2, 1), (3, 1), (3, 2), (4, 2), (5, 2), (5, 3), (6, 3)])
def test_dicke_circuit_prepares_exact_dicke_state(n, k):
    probs = Statevector(dicke_state_circuit(n, k)).probabilities()
    weights = basis_matrix(n).sum(axis=1)
    expected = np.where(weights == k, 1.0 / comb(n, k), 0.0)
    assert np.allclose(probs, expected, atol=1e-10)


@pytest.mark.parametrize("mixer,init", [("x", "plus"), ("xy_ring", "dicke")])
@pytest.mark.parametrize("n,p", [(3, 1), (4, 2), (5, 3)])
def test_exact_simulator_matches_qiskit_statevector(mixer, init, n, p):
    problem = generate_portfolio_instance(n, seed=n).to_problem()
    rho = None if mixer == "x" else 0.0
    ising = problem.penalized_qubo(rho).to_ising()
    params = np.random.default_rng(0).uniform(-1.0, 1.0, size=2 * p)

    circuit = build_qaoa_circuit(ising, p, mixer=mixer, init=init, k=problem.k)
    psi_qiskit = Statevector(bind(circuit, params)).data
    psi_fast = ExactQAOASimulator(ising, p, mixer=mixer, init=init, k=problem.k).statevector(params)

    fidelity = abs(np.vdot(psi_qiskit, psi_fast)) ** 2
    assert fidelity == pytest.approx(1.0, abs=1e-10)


@pytest.mark.parametrize("n,k,p", [(4, 2, 2), (6, 3, 2)])
def test_xy_mixer_keeps_all_probability_on_feasible_subspace(n, k, p):
    problem = generate_portfolio_instance(n, k=k, seed=1).to_problem()
    ising = problem.penalized_qubo(0.0).to_ising()
    sim = ExactQAOASimulator(ising, p, mixer="xy_ring", init="dicke", k=k)
    probs = sim.probabilities(np.random.default_rng(3).uniform(-2, 2, size=2 * p))
    weights = basis_matrix(n).sum(axis=1)
    assert probs[weights != k].sum() < 1e-12


def test_sample_counts_sum_to_shots_and_use_little_endian_keys():
    probs = np.zeros(8)
    probs[0b011] = 1.0  # x_0 = x_1 = 1
    counts = sample_counts(probs, 100, np.random.default_rng(0))
    assert counts == {"011": 100}
