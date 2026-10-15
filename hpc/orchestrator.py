"""Pipeline híbrido instrumentado (auditoria §6, Epic D):

    CPU: instância -> problema canônico -> QUBO/Ising -> oráculo clássico
    CPU: laço variacional (simulação ideal exata) -> parâmetros
    backend: circuito otimizado -> ideal exato | Aer CPU/GPU (ruído/fake) | QPU (opt-in)
    CPU: contagens -> métricas unificadas

Cada estágio tem tempo próprio; o registro diz em qual dispositivo a execução realmente ocorreu.
"""
from __future__ import annotations

import time
from typing import Optional

from optimization.canonical_qubo import CardinalityProblem
from optimization.classical_qubo import solve_enumeration
from quantum.ansatz import bind, build_qaoa_circuit
from quantum.backends import AerBackend, ExactStatevectorBackend, IBMQPUBackend, QPUBudget
from quantum.backends.base import BackendAdapter
from quantum.measurement import analyze_counts
from quantum.resources import estimate_resources
from quantum.runner import QAOAConfig, run_qaoa

from .profiling import StageTimer, process_peak_rss_mb, traced_memory


def make_backend(spec: dict, allow_qpu: bool = False) -> BackendAdapter:
    kind = spec.get("type", "ideal_exact")
    if kind == "ideal_exact":
        return ExactStatevectorBackend()
    if kind == "aer":
        return AerBackend(regime=spec.get("regime", "ideal"), fake_backend=spec.get("fake_backend"),
                          device=spec.get("device", "CPU"), allow_cpu_fallback=spec.get("allow_cpu_fallback", True),
                          noise_params=spec.get("noise_params"), optimization_level=spec.get("optimization_level", 1),
                          method=spec.get("method", "automatic"))
    if kind == "ibm_qpu":
        budget = QPUBudget(**spec.get("budget", {}))
        return IBMQPUBackend(spec["backend_name"], allow_qpu=allow_qpu, budget=budget,
                             dry_run=spec.get("dry_run", True), timeout_s=spec.get("timeout_s", 900.0))
    raise ValueError(f"tipo de backend desconhecido: {kind}")


def run_pipeline(problem: CardinalityProblem, cfg: QAOAConfig, backend: Optional[BackendAdapter] = None,
                 enumeration: Optional[dict] = None, profile_memory: bool = True) -> dict:
    timer = StageTimer()
    t_start = time.perf_counter()
    with traced_memory(profile_memory) as mem:
        with timer.stage("time_classical_reference"):
            enumeration = enumeration or solve_enumeration(problem)
        qaoa = run_qaoa(problem, cfg, enumeration=enumeration)
        for key in ("time_preprocess", "time_build", "time_classical_opt"):
            timer.add(key, qaoa.record["timings"][key])

        record = dict(qaoa.record)
        record["ideal_sampling"] = {k: record.pop(k) for k in list(record) if k in _SAMPLED_KEYS}
        record["resources"] = estimate_resources(problem.n, problem.k, cfg.p, cfg.mixer, len(qaoa.ising.edges()),
                                                 int((qaoa.ising.h != 0).sum()))
        record["execution"] = None
        counts = qaoa.extras["counts"]
        if backend is not None:
            with timer.stage("time_build_circuit"):
                circuit = bind(build_qaoa_circuit(qaoa.ising, cfg.p, cfg.mixer, cfg.init, problem.k, measure=True),
                               qaoa.params_final)
            execution = backend.run(circuit, shots=cfg.shots, seed=cfg.seed)
            timer.add("time_transpile", execution.elapsed.get("time_transpile"))
            timer.add("time_quantum_execution", execution.elapsed.get("time_quantum_execution"))
            record["execution"] = execution.to_dict(include_counts=False)
            counts = execution.counts
            with timer.stage("time_postprocess"):
                if counts:
                    record["execution"]["metrics"] = analyze_counts(problem, counts, qaoa.f_star, qaoa.qubo.evaluate)
                else:
                    record["execution"]["metrics"] = None
    record["memory"] = {"peak_traced_mb": mem["peak_traced_mb"], "process_peak_rss_mb": process_peak_rss_mb()}
    record["elapsed"] = {**timer.times, "time_total": time.perf_counter() - t_start}
    record["classical_reference"] = {k: enumeration[k] for k in
                                     ("method", "objective", "n_optimal", "n_feasible", "time_s", "certified")}
    return {"record": record, "counts": counts}


_SAMPLED_KEYS = {
    "shots", "n_distinct_bitstrings", "feasible_shots", "feasible_rate", "invalid_shot_rate", "optimal_shots",
    "p_optimum", "p_optimum_ci95", "cardinality_violation_hist", "most_probable_bitstring",
    "most_probable_is_feasible", "energy_mean", "f_mean_feasible", "status", "solution", "solution_bitstring",
    "solution_labels", "f_best", "gap_abs", "gap_rel", "is_optimal",
}
