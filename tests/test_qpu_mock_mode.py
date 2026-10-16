"""T09/T11/T14 — guardas do adaptador QPU; só mocks injetados, nenhuma chamada de rede."""
import sys

import numpy as np
import pytest
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import CouplingMap

from hpc.orchestrator import make_backend
from optimization.instance import generate_portfolio_instance
from quantum.ansatz import bind, build_qaoa_circuit
from quantum.backends import IBMQPUBackend, QPUBudget, QPUNotAllowed, QPUUnavailable


@pytest.fixture
def circuit():
    problem = generate_portfolio_instance(4, seed=0).to_problem()
    return bind(build_qaoa_circuit(problem.penalized_qubo().to_ising(), 1, measure=True), np.array([0.3, 0.2]))


class _Counts:
    def __init__(self, counts):
        self._c = counts

    def get_counts(self):
        return self._c


class _Pub:
    def __init__(self, counts):
        self.data = type("D", (), {"meas": _Counts(counts)})()


class MockJob:
    def __init__(self, mode):
        self.mode = mode
        self.cancelled = False

    def job_id(self):
        return "mock-job-1"

    def result(self, timeout=None):
        if self.mode == "timeout":
            raise TimeoutError("fila")
        if self.mode == "fail":
            raise RuntimeError("job falhou no provedor")
        return [_Pub({"0011": 60, "0101": 40})]

    def cancel(self):
        self.cancelled = True

    def metrics(self):
        return {"usage": {"quantum_seconds": 1.5, "seconds": 2.0}}


class MockSampler:
    def __init__(self, mode, calls):
        self.mode, self.calls = mode, calls

    def run(self, pubs, shots):
        self.calls.append(shots)
        self.job = MockJob(self.mode)
        return self.job


class MockService:
    def backend(self, name):
        return GenericBackendV2(num_qubits=5, coupling_map=CouplingMap.from_line(5), seed=1)


def _qpu(mode="ok", calls=None, **kw):
    calls = [] if calls is None else calls
    holder = {}

    def factory(backend):
        holder["sampler"] = MockSampler(mode, calls)
        return holder["sampler"]

    return IBMQPUBackend("mock_backend", allow_qpu=True, service=MockService(), sampler_factory=factory, **kw), holder


def test_without_allow_flag_nothing_is_imported_or_called():
    with pytest.raises(QPUNotAllowed):
        IBMQPUBackend("ibm_any")
    with pytest.raises(QPUNotAllowed):
        make_backend({"type": "ibm_qpu", "backend_name": "ibm_any"})
    assert "qiskit_ibm_runtime" not in sys.modules


def test_real_execution_refused_in_ci(monkeypatch):
    monkeypatch.setenv("CI", "true")
    with pytest.raises(QPUNotAllowed):
        IBMQPUBackend("ibm_any", allow_qpu=True)


def test_missing_credentials_is_blocked_by_configuration(monkeypatch, circuit):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("QISKIT_IBM_TOKEN", raising=False)
    with pytest.raises(QPUUnavailable, match="BLOCKED_BY_CONFIGURATION"):
        IBMQPUBackend("ibm_any", allow_qpu=True).run(circuit, shots=100)


def test_mock_job_completes_but_is_never_labelled_real_hardware(circuit):
    qpu, _ = _qpu()
    res = qpu.run(circuit, shots=100, seed=0)
    assert res.status == "completed" and res.job_id == "mock-job-1"
    assert res.is_real_hardware is False
    assert sum(res.counts.values()) == 100
    assert res.transpile_metrics["target_supported"]


@pytest.mark.parametrize("mode,status", [("timeout", "timeout"), ("fail", "failed")])
def test_timeout_and_failed_jobs_are_recovered(circuit, mode, status):
    qpu, holder = _qpu(mode=mode)
    res = qpu.run(circuit, shots=100)
    assert res.status == status and res.counts == {} and res.job_id == "mock-job-1"
    if mode == "timeout":
        assert holder["sampler"].job.cancelled


def test_budget_limits_are_enforced(circuit):
    qpu, _ = _qpu(budget=QPUBudget(max_shots_per_job=200, max_jobs=1, max_total_shots=200))
    with pytest.raises(QPUNotAllowed):
        qpu.run(circuit, shots=500)
    qpu.run(circuit, shots=100)
    with pytest.raises(QPUNotAllowed):
        qpu.run(circuit, shots=100)


def test_dry_run_validates_isa_without_submitting(circuit):
    calls = []
    qpu, _ = _qpu(calls=calls, dry_run=True)
    res = qpu.run(circuit, shots=100)
    assert res.status == "dry_run" and res.backend_type == "ibm_qpu_dry_run"
    assert calls == [] and res.is_real_hardware is False
