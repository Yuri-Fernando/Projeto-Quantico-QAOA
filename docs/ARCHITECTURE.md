# Arquitetura

```text
instância (portfolio | shift_scheduling)
   └─► CardinalityProblem  (Q triangular, k, objective_id)          optimization/canonical_qubo.py
         ├─► baselines no MESMO objetivo                            optimization/classical_qubo.py
         │     enumeração · MILP McCormick (HiGHS) · relaxação LP     optimization/heuristics.py
         │     simulated annealing · amostragem aleatória viável
         └─► QUBO(ρ) ─► Ising(h, J, offset) ─► SparsePauliOp
               └─► circuito QAOA (mixer X | XY+Dicke)               quantum/ansatz.py
                     ├─► laço variacional (CPU, ideal exato)        quantum/runner.py, quantum/simulator.py
                     └─► backend                                    quantum/backends/
                           ├─ ideal_exact (Statevector + amostragem)
                           ├─ Aer CPU/GPU · ruído · backend fake    quantum/noise.py, quantum/transpilation.py
                           └─ IBM QPU (opt-in, orçamento, dry-run)
                     └─► métricas unificadas                        quantum/measurement.py
orquestração e tempos por estágio                                   hpc/orchestrator.py, hpc/profiling.py
detecção de dispositivos                                            hpc/devices.py
experimentos (config → manifest → records → summary)                experiments/
```

## Pacotes

| Pacote | Responsabilidade | Testes |
|---|---|---|
| `optimization/` | v0.2.0 (LP, MILP, estocástico, Benders, QAOA via qiskit_algorithms) + problema canônico, baselines exatos e heurísticas, segundo domínio | `test_lp/milp/stochastic/benders/qaoa/instance`, `test_qubo_equivalence`, `test_milp_qubo_parity`, `test_instance_generation`, `test_scheduling`, `test_legacy_penalty` |
| `quantum/` | circuito, simulação exata, medição/estatística, transpilation, ruído, backends, recursos, runner | `test_ansatz`, `test_feasibility`, `test_sampling_statistics`, `test_transpilation`, `test_noise_reproducibility`, `test_qpu_mock_mode` |
| `hpc/` | dispositivos, profiling, pipeline híbrido | `test_cpu_gpu_parity` |
| `experiments/` | CLI, schemas/manifest, análise, demo | `test_experiments` |
| `benchmarks/` | trilha `model_comparison` + atalhos da trilha `algorithm_benchmark` | `test_experiments` |
| `legacy/v1/` | rascunho original, não executável | `test_legacy_penalty` |

## Resultado unificado de execução

`quantum.backends.base.ExecutionResult`:

```text
backend_type        ideal_exact | aer_ideal | aer_noisy | aer_fake_backend | ibm_qpu | ibm_qpu_dry_run
backend_name, device (CPU|GPU|QPU), is_real_hardware
shots, counts, seed, circuit_hash, physical_qubits
noise_regime, noise_model_hash
transpile_metrics   depth/2Q lógico e físico, SWAPs, layout, Target ok, tempo
elapsed             time_transpile, time_quantum_execution, time_total, ...
status, job_id, warnings, solver_versions, metadata
```

## Decisões

- **Circuito explícito** (rz/rzz/rx/rxx/ryy) em vez de `QAOAAnsatz`: convenção visível e paridade
  testável com o simulador vetorizado.
- **Simulador vetorizado próprio** para o laço variacional ideal: exato (fidelidade 1 com o
  `Statevector` do Qiskit em teste) e barato o suficiente para varreduras de milhares de execuções.
  Ruído e topologia usam Aer.
- **McCormick em vez de MIQP**: HiGHS não resolve MIQP; a linearização é exata para binários.
- **GPU/QPU atrás de guardas**: a detecção é real (`available_devices()`, `nvidia-smi`) e a ausência é
  registrada como resultado, nunca simulada.
- **Sem Dask/Ray/Streamlit**: a escala atual não justifica (auditoria §11).
