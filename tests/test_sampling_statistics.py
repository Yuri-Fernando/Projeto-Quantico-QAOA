"""T04/T05/T06/T15 — probabilidades válidas, contagens somam shots, determinismo por seed, ICs."""
import numpy as np
import pytest

from optimization.instance import generate_portfolio_instance
from quantum.ansatz import bind, build_qaoa_circuit
from quantum.backends import AerBackend, ExactStatevectorBackend
from quantum.measurement import bootstrap_ci, wilson_interval
from quantum.runner import QAOAConfig, run_qaoa


@pytest.fixture(scope="module")
def problem():
    return generate_portfolio_instance(5, seed=4).to_problem()


def test_probabilities_are_non_negative_and_normalized(problem):
    run = run_qaoa(problem, QAOAConfig(p=2, maxiter=30, seed=0))
    assert np.all(run.probabilities >= 0)
    assert run.probabilities.sum() == pytest.approx(1.0, abs=1e-12)
    assert sum(run.extras["counts"].values()) == run.record["shots"] == 1024


@pytest.mark.parametrize("backend", [ExactStatevectorBackend(), AerBackend(regime="ideal")], ids=["exact", "aer"])
def test_backend_counts_sum_to_shots(problem, backend):
    run = run_qaoa(problem, QAOAConfig(p=1, maxiter=20, seed=0))
    circuit = bind(build_qaoa_circuit(run.ising, 1, measure=True), run.params_final)
    res = backend.run(circuit, shots=777, seed=3)
    assert sum(res.counts.values()) == 777
    assert all(c >= 0 for c in res.counts.values())
    assert res.is_real_hardware is False and res.device == "CPU"


def test_same_seed_is_deterministic(problem):
    cfg = QAOAConfig(p=2, optimizer="spsa", init_strategy="random", objective_mode="sampled", maxiter=20, seed=9)
    a, b = run_qaoa(problem, cfg), run_qaoa(problem, cfg)
    assert a.record["params_final"] == b.record["params_final"]
    assert a.extras["counts"] == b.extras["counts"]


def test_seed_change_varies_samples_within_binomial_bounds(problem):
    """T06: seeds diferentes mudam as amostras, mas P(ótimo) amostrado fica coerente com o exato."""
    estimates = []
    for seed in range(6):
        rec = run_qaoa(problem, QAOAConfig(p=1, init_strategy="linear_ramp", maxiter=30, seed=seed,
                                           shots=2000)).record
        p, phat = rec["p_optimum_exact"], rec["p_optimum"]
        assert abs(phat - p) <= 6 * np.sqrt(p * (1 - p) / 2000) + 1e-3
        estimates.append(phat)
    assert len(set(estimates)) > 1  # amostragem realmente varia com a seed


def test_wilson_and_bootstrap_intervals():
    lo, hi = wilson_interval(30, 100)
    assert 0.0 <= lo < 0.30 < hi <= 1.0
    assert wilson_interval(0, 50)[0] == 0.0
    values = np.random.default_rng(0).normal(1.0, 0.1, size=30)
    ci = bootstrap_ci(values, seed=1)
    assert ci[0] <= values.mean() <= ci[1]
    assert ci == bootstrap_ci(values, seed=1)
    assert bootstrap_ci([None, 2.0]) == [2.0, 2.0]
