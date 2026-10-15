"""Adaptador IBM Quantum (QPU real) — opt-in explícito, orçamento e nada de rede por acidente.

Estado: IMPLEMENTADO e testado SOMENTE com serviço/sampler injetados (mocks). O caminho real está
``BLOCKED_BY_CONFIGURATION``: ``qiskit-ibm-runtime`` não está instalado neste ambiente e não há
credenciais. A API do Runtime muda entre versões (primitives server-side × client-side, nomes de
canal) — confira a documentação da versão instalada antes do primeiro uso real.

Guardas, em ordem (T11/T14):
1. ``allow_qpu=True`` é obrigatório (na CLI: ``--allow-qpu``); sem ele nada é importado nem chamado;
2. dentro de CI (variável ``CI`` definida) a execução real é recusada;
3. credenciais só por variável de ambiente (``QISKIT_IBM_TOKEN`` por padrão; o valor nunca é logado);
4. orçamento: shots por job, número de jobs e shots totais;
5. ``dry_run=True`` transpila para o ``Target`` do backend e valida o circuito ISA SEM submeter job.

``is_real_hardware=True`` somente quando há ``job_id`` e contagens de um serviço real (não injetado).
"""
from __future__ import annotations

import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Optional

from qiskit import QuantumCircuit

from ..transpilation import transpile_with_metrics
from .base import BackendAdapter, ExecutionResult, circuit_hash


class QPUNotAllowed(PermissionError):
    pass


class QPUUnavailable(RuntimeError):
    """Recurso não configurado (``BLOCKED_BY_CONFIGURATION``)."""


@dataclass
class QPUBudget:
    max_shots_per_job: int = 4000
    max_jobs: int = 1
    max_total_shots: int = 4000


class IBMQPUBackend(BackendAdapter):
    backend_type = "ibm_qpu"

    def __init__(self, backend_name: str, allow_qpu: bool = False, budget: Optional[QPUBudget] = None,
                 dry_run: bool = False, timeout_s: float = 900.0, token_env: str = "QISKIT_IBM_TOKEN",
                 instance_env: str = "QISKIT_IBM_INSTANCE", channel: str = "ibm_quantum_platform",
                 service=None, sampler_factory: Optional[Callable] = None, optimization_level: int = 1):
        if not allow_qpu:
            raise QPUNotAllowed("execução em QPU exige opt-in explícito (allow_qpu=True / --allow-qpu)")
        injected = service is not None
        if os.environ.get("CI") and not injected:
            raise QPUNotAllowed("execução em QPU real é proibida em CI")
        self.backend_name = backend_name
        self.budget = budget or QPUBudget()
        self.dry_run = dry_run
        self.timeout_s = timeout_s
        self.token_env = token_env
        self.instance_env = instance_env
        self.channel = channel
        self.optimization_level = optimization_level
        self._service = service
        self._service_is_real = not injected
        self._sampler_factory = sampler_factory
        self.jobs_submitted = 0
        self.shots_submitted = 0

    # ------------------------------------------------------------------ serviço
    def _get_service(self):
        if self._service is not None:
            return self._service
        token = os.environ.get(self.token_env)
        if not token:
            raise QPUUnavailable(f"BLOCKED_BY_CONFIGURATION: variável {self.token_env} não definida")
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
        except ImportError as exc:
            raise QPUUnavailable("BLOCKED_BY_CONFIGURATION: qiskit-ibm-runtime não instalado") from exc
        kwargs = {"channel": self.channel, "token": token}
        if os.environ.get(self.instance_env):
            kwargs["instance"] = os.environ[self.instance_env]
        self._service = QiskitRuntimeService(**kwargs)
        return self._service

    def _make_sampler(self, backend):
        if self._sampler_factory is not None:
            return self._sampler_factory(backend)
        from qiskit_ibm_runtime import SamplerV2

        return SamplerV2(mode=backend)

    def _check_budget(self, shots: int) -> None:
        b = self.budget
        if shots > b.max_shots_per_job:
            raise QPUNotAllowed(f"shots={shots} excede max_shots_per_job={b.max_shots_per_job}")
        if self.jobs_submitted + 1 > b.max_jobs:
            raise QPUNotAllowed(f"limite de jobs atingido ({b.max_jobs})")
        if self.shots_submitted + shots > b.max_total_shots:
            raise QPUNotAllowed(f"limite de shots totais atingido ({b.max_total_shots})")

    # ------------------------------------------------------------------ execução
    def run(self, circuit: QuantumCircuit, shots: int, seed: Optional[int] = None) -> ExecutionResult:
        t_start = time.perf_counter()
        self._check_budget(shots)
        service = self._get_service()
        backend = service.backend(self.backend_name)
        isa, tmetrics = transpile_with_metrics(circuit, backend, self.optimization_level, 0 if seed is None else seed)
        common = dict(backend_name=self.backend_name, shots=shots, seed=seed, circuit_hash=circuit_hash(circuit),
                      physical_qubits=tmetrics["initial_layout"], transpile_metrics=tmetrics)
        if not tmetrics["target_supported"]:
            return ExecutionResult(backend_type=self.backend_type, is_real_hardware=False, device="QPU",
                                   counts={}, status="failed", warnings=["circuito ISA rejeitado pelo Target"],
                                   elapsed={"time_total": time.perf_counter() - t_start}, **common)
        if self.dry_run:
            return ExecutionResult(backend_type="ibm_qpu_dry_run", is_real_hardware=False, device="QPU",
                                   counts={}, status="dry_run", warnings=["dry_run: nenhum job submetido"],
                                   elapsed={"time_transpile": tmetrics["transpile_time_s"],
                                            "time_total": time.perf_counter() - t_start}, **common)

        sampler = self._make_sampler(backend)
        t_submit = time.perf_counter()
        job = sampler.run([isa], shots=shots)
        self.jobs_submitted += 1
        self.shots_submitted += shots
        job_id = job.job_id()
        warnings = [] if self._service_is_real else ["serviço injetado (mock): não é hardware real"]
        try:
            result = job.result(timeout=self.timeout_s)
        except TimeoutError:
            _safe_cancel(job)
            return ExecutionResult(backend_type=self.backend_type, is_real_hardware=False, device="QPU", counts={},
                                   status="timeout", job_id=job_id, warnings=warnings + ["timeout: job cancelado"],
                                   elapsed={"time_total": time.perf_counter() - t_start}, **common)
        except Exception as exc:  # job falhou/cancelado no provedor
            return ExecutionResult(backend_type=self.backend_type, is_real_hardware=False, device="QPU", counts={},
                                   status="failed", job_id=job_id, warnings=warnings + [f"job falhou: {exc}"],
                                   elapsed={"time_total": time.perf_counter() - t_start}, **common)
        t_done = time.perf_counter()
        counts = {k.replace(" ", ""): int(v) for k, v in result[0].data.meas.get_counts().items()}
        usage = _job_metrics(job)
        return ExecutionResult(
            backend_type=self.backend_type, is_real_hardware=bool(job_id and counts and self._service_is_real),
            device="QPU", counts=counts, status="completed", job_id=job_id, warnings=warnings,
            elapsed={"time_transpile": tmetrics["transpile_time_s"], "time_submit_to_result": t_done - t_submit,
                     "time_quantum_execution": usage.get("quantum_seconds"), "time_total": t_done - t_start},
            metadata={"job_metrics": usage, "channel": self.channel}, **common,
        )


def _safe_cancel(job) -> None:
    try:
        job.cancel()
    except Exception:
        pass


def _job_metrics(job) -> dict:
    try:
        metrics = job.metrics() or {}
    except Exception:
        return {}
    usage = metrics.get("usage", {}) if isinstance(metrics, dict) else {}
    return {"quantum_seconds": usage.get("quantum_seconds"), "seconds": usage.get("seconds"),
            "timestamps": metrics.get("timestamps") if isinstance(metrics, dict) else None}
