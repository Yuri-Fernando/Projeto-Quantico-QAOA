"""Ruído local: reprodutível por seed, hash estável e degradação mensurável da viabilidade."""
import pytest

from optimization.instance import generate_portfolio_instance
from quantum.ansatz import bind, build_qaoa_circuit
from quantum.backends import AerBackend
from quantum.measurement import analyze_counts
from quantum.noise import build_noise_model, noise_model_hash
from quantum.runner import QAOAConfig, run_qaoa


@pytest.fixture(scope="module")
def xy_run():
    problem = generate_portfolio_instance(4, seed=1).to_problem()
    run = run_qaoa(problem, QAOAConfig(p=1, mixer="xy_ring", maxiter=40, seed=0))
    circuit = bind(build_qaoa_circuit(run.ising, 1, "xy_ring", "dicke", problem.k, measure=True), run.params_final)
    return problem, run, circuit


def test_same_seed_gives_identical_noisy_counts(xy_run):
    _, _, circuit = xy_run
    backend = AerBackend(regime="readout+depolarizing")
    assert backend.run(circuit, 1000, seed=5).counts == backend.run(circuit, 1000, seed=5).counts


def test_noise_hash_is_stable_and_distinguishes_regimes():
    h1 = noise_model_hash(build_noise_model("depolarizing"))
    assert h1 == noise_model_hash(build_noise_model("depolarizing"))
    assert h1 != noise_model_hash(build_noise_model("readout"))
    assert noise_model_hash(build_noise_model("ideal")) is None


def test_readout_noise_breaks_cardinality_preservation(xy_run):
    """Ideal: mixer XY mantém 100% das amostras viáveis. Com 10% de erro de leitura, não."""
    problem, run, circuit = xy_run
    ideal = analyze_counts(problem, AerBackend("ideal").run(circuit, 4000, seed=1).counts, run.f_star)
    readout = AerBackend("readout", noise_params={"p_meas": 0.1})
    noisy = analyze_counts(problem, readout.run(circuit, 4000, seed=1).counts, run.f_star)
    assert ideal["feasible_rate"] == 1.0
    assert noisy["feasible_rate"] < 0.9


def test_fake_backend_noise_runs_with_layout(xy_run):
    problem, run, circuit = xy_run
    res = AerBackend(regime="backend", fake_backend="generic_line_4").run(circuit, 500, seed=2)
    assert res.backend_type == "aer_fake_backend" and res.is_real_hardware is False
    assert sum(res.counts.values()) == 500 and res.noise_model_hash
    assert res.transpile_metrics["target_supported"]
