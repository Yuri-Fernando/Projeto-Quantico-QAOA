"""T12 — paridade CPU×GPU quando o Aer tem GPU; caso contrário, skip explícito e fallback rotulado."""
import numpy as np
import pytest

from hpc.devices import aer_available_devices, aer_gpu_available, detect_devices
from optimization.instance import generate_portfolio_instance
from quantum.ansatz import bind, build_qaoa_circuit
from quantum.backends import AerBackend, GPUUnavailable


def _circuit():
    problem = generate_portfolio_instance(6, seed=0).to_problem()
    ising = problem.penalized_qubo().to_ising()
    return bind(build_qaoa_circuit(ising, 2, measure=True), np.linspace(0.1, 0.6, 4))


@pytest.mark.skipif(not aer_gpu_available(),
                    reason=f"GPU indisponível no qiskit-aer (available_devices={aer_available_devices()})")
def test_cpu_gpu_distributions_match():  # pragma: no cover - depende de hardware
    circuit = _circuit()
    cpu = AerBackend(device="CPU").run(circuit, 20000, seed=1)
    gpu = AerBackend(device="GPU", allow_cpu_fallback=False).run(circuit, 20000, seed=1)
    assert gpu.device == "GPU"
    keys = set(cpu.counts) | set(gpu.counts)
    tvd = 0.5 * sum(abs(cpu.counts.get(k, 0) - gpu.counts.get(k, 0)) / 20000 for k in keys)
    assert tvd < 0.03


@pytest.mark.skipif(aer_gpu_available(), reason="GPU disponível: o teste de fallback não se aplica")
def test_gpu_request_without_gpu_never_claims_gpu():
    with pytest.raises(GPUUnavailable):
        AerBackend(device="GPU", allow_cpu_fallback=False)
    res = AerBackend(device="GPU", allow_cpu_fallback=True).run(_circuit(), 100, seed=0)
    assert res.device == "CPU"
    assert any("gpu_requested_but_unavailable" in w for w in res.warnings)
    assert res.metadata["requested_device"] == "GPU"


def test_detect_devices_reports_consistent_gpu_status():
    info = detect_devices()
    assert info["aer_gpu_available"] == ("GPU" in info["aer_available_devices"])
    assert info["gpu_status"] in {"available", "host_has_nvidia_gpu_but_qiskit_aer_build_is_cpu_only",
                                  "no_gpu_detected"}
