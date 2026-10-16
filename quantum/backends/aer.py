"""Backends locais: statevector exato e Qiskit Aer (CPU/GPU, ideal/ruidoso/fake)."""
from __future__ import annotations

import time
from typing import Optional

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from hpc.devices import aer_available_devices

from ..noise import build_noise_model, get_fake_backend, noise_model_hash
from ..simulator import sample_counts
from ..transpilation import basis_only_transpile, logical_metrics, transpile_with_metrics
from .base import BackendAdapter, ExecutionResult, circuit_hash


class GPUUnavailable(RuntimeError):
    pass


class ExactStatevectorBackend(BackendAdapter):
    """Evolução ideal exata (``Statevector``) + amostragem multinomial finita com seed."""

    backend_type = "ideal_exact"

    def run(self, circuit: QuantumCircuit, shots: int, seed: Optional[int] = None) -> ExecutionResult:
        t0 = time.perf_counter()
        bare = circuit.remove_final_measurements(inplace=False)
        probs = Statevector(bare).probabilities()
        t_exec = time.perf_counter() - t0
        counts = sample_counts(probs, shots, np.random.default_rng(seed))
        return ExecutionResult(
            backend_type=self.backend_type, backend_name="qiskit.quantum_info.Statevector",
            is_real_hardware=False, device="CPU", shots=shots, counts=counts, status="completed", seed=seed,
            circuit_hash=circuit_hash(bare), noise_regime="ideal",
            transpile_metrics=logical_metrics(bare),
            elapsed={"time_quantum_execution": t_exec, "time_total": time.perf_counter() - t0},
            metadata={"probabilities_exact": True},
        )


class AerBackend(BackendAdapter):
    """Qiskit Aer. ``fake_backend`` impõe topologia/base do backend; ``regime`` define o ruído.

    GPU: só é usada se ``"GPU" in AerSimulator().available_devices()``. Caso contrário, com
    ``allow_cpu_fallback=True`` roda em CPU e registra o aviso; com ``False`` levanta ``GPUUnavailable``.
    Nunca reporta ``device="GPU"`` sem a GPU ter sido de fato usada pelo Aer.
    """

    def __init__(self, regime: str = "ideal", fake_backend: Optional[str] = None, device: str = "CPU",
                 allow_cpu_fallback: bool = True, noise_params: Optional[dict] = None,
                 optimization_level: int = 1, method: str = "automatic"):
        self.regime = regime
        self.fake_backend_name = fake_backend
        self.requested_device = device.upper()
        self.optimization_level = optimization_level
        self.method = method
        self.warnings = []
        devices = aer_available_devices()
        if self.requested_device == "GPU" and "GPU" not in devices:
            if not allow_cpu_fallback:
                raise GPUUnavailable(f"GPU não disponível no qiskit-aer instalado (available_devices={devices})")
            self.warnings.append(f"gpu_requested_but_unavailable(available_devices={list(devices)}): executado em CPU")
            self.device = "CPU"
        else:
            self.device = self.requested_device
        self.fake = get_fake_backend(fake_backend) if fake_backend else None
        self.noise_model = build_noise_model(regime, noise_params, backend=self.fake)
        if self.fake is not None:
            self.backend_type = "aer_fake_backend"
        else:
            self.backend_type = "aer_ideal" if regime == "ideal" else "aer_noisy"
        self.simulator = AerSimulator(noise_model=self.noise_model, device=self.device, method=method)

    @property
    def name(self) -> str:
        base = self.fake.name if self.fake is not None else "aer_simulator"
        return f"{base}[{self.regime}]"

    def run(self, circuit: QuantumCircuit, shots: int, seed: Optional[int] = None) -> ExecutionResult:
        t_start = time.perf_counter()
        seed = 0 if seed is None else int(seed)
        if self.fake is not None:
            isa, tmetrics = transpile_with_metrics(circuit, self.fake, self.optimization_level, seed)
            physical = tmetrics["initial_layout"]
        else:
            t0 = time.perf_counter()
            if self.noise_model is not None:
                isa = basis_only_transpile(circuit, optimization_level=self.optimization_level, seed_transpiler=seed)
            else:
                isa = transpile(circuit, self.simulator, optimization_level=self.optimization_level,
                                seed_transpiler=seed)
            tmetrics = {**logical_metrics(circuit), "transpile_time_s": time.perf_counter() - t0,
                        "depth_physical": isa.depth(), "count_ops_physical": dict(isa.count_ops()),
                        "two_qubit_gates_physical": sum(1 for i in isa.data if i.operation.num_qubits == 2
                                                        and i.operation.name != "barrier"),
                        "swap_count": 0, "coupling": "all_to_all"}
            physical = None
        t0 = time.perf_counter()
        result = self.simulator.run(isa, shots=shots, seed_simulator=seed).result()
        t_exec = time.perf_counter() - t0
        counts = {k.replace(" ", ""): int(v) for k, v in result.get_counts().items()}
        meta = getattr(result.results[0], "metadata", {}) if result.results else {}
        used_device = meta.get("device", self.device)
        warnings = list(self.warnings)
        if str(used_device).upper() != self.device:
            warnings.append(f"aer_reported_device={used_device}")
        return ExecutionResult(
            backend_type=self.backend_type, backend_name=self.name, is_real_hardware=False,
            device=str(used_device).upper(), shots=shots, counts=counts, status="completed", seed=seed,
            circuit_hash=circuit_hash(circuit), physical_qubits=physical, noise_regime=self.regime,
            noise_model_hash=noise_model_hash(self.noise_model), transpile_metrics=tmetrics,
            elapsed={"time_transpile": tmetrics.get("transpile_time_s", 0.0), "time_quantum_execution": t_exec,
                     "time_aer_reported": float(getattr(result, "time_taken", 0.0) or 0.0),
                     "time_total": time.perf_counter() - t_start},
            warnings=warnings,
            metadata={"requested_device": self.requested_device, "method": self.method},
        )
