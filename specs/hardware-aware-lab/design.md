# Design — v0.3.0

## Componentes

| Pacote / módulo | Papel | Requisitos |
|---|---|---|
| `optimization/canonical_qubo.py` | `CardinalityProblem`, `QUBO`, `IsingHamiltonian`, penalidades, bitstrings | FR-1..3 |
| `optimization/classical_qubo.py` | enumeração, MILP linearizado, relaxação LP | FR-4 |
| `optimization/heuristics.py` | simulated annealing (troca preserva Σx=k), amostragem aleatória viável | FR-4 |
| `optimization/instance.py` | + `generate_portfolio_instance(n, k, seed)`, validação, `to_problem()` | FR-9 |
| `optimization/scheduling.py` | segundo domínio (tarefas × turno × conflitos) | FR-13 |
| `quantum/ansatz.py` | circuito QAOA explícito (rz/rzz/rx; rxx/ryy), Dicke (Bärtschi–Eidenbenz) | FR-5 |
| `quantum/simulator.py` | simulador exato vetorizado (custo diagonal) para varreduras rápidas | FR-5 |
| `quantum/measurement.py` | análise de contagens/probabilidades, Wilson, bootstrap | FR-6 |
| `quantum/transpilation.py` | métricas lógicas/físicas, SWAPs, layout | FR-7 |
| `quantum/noise.py` | regimes de ruído, hash | FR-8 |
| `quantum/backends/` | `ExecutionResult`, backends exato/Aer (CPU/GPU)/IBM QPU | FR-8, FR-10, FR-11 |
| `quantum/resources.py` | memória statevector/densidade, contagens | FR-9 |
| `quantum/runner.py` | laço variacional instrumentado (COBYLA/SPSA, init, seeds, tempos) | FR-5 |
| `hpc/` | detecção de dispositivos, perfil (tempo/memória), orquestrador híbrido | FR-10 |
| `experiments/` | configs YAML, schemas/manifest, `run`, `analyze`, `demo` | FR-12 |
| `benchmarks/` | `compare_methods` (modelos) + wrappers `fair_qubo_benchmark`, `scalability` | FR-14 |

## Interfaces centrais

```text
CardinalityProblem(Q_upper, constant, k, labels, objective_id)
  .evaluate(x) -> f(x)          .penalized_qubo(rho) -> QUBO          .instance_hash
QUBO(Q_upper, offset, rho).to_ising() -> IsingHamiltonian(h, J, offset).to_sparse_pauli_op()
build_qaoa_circuit(ising, p, mixer, init, k) -> QuantumCircuit (params γ_0..γ_{p-1}, β_0..β_{p-1})
run_qaoa(problem, config, backend) -> dict (counts, métricas, tempos, parâmetros, metadados)
ExecutionResult: backend_type, backend_name, is_real_hardware, device, shots, counts, seed,
                 elapsed, transpile_metrics, status, job_id, warnings
```

Ordem de bits: qubit `i` ↔ variável `x_i`; na string de contagem do Qiskit, `x_i` é o caractere
`n−1−i` (little-endian). `x_i = (1 − z_i)/2`, `z_i ∈ {+1, −1}`.

## Decisões e alternativas descartadas

- Circuito QAOA explícito em vez de `QAOAAnsatz`: controle total de convenção e paridade testável com o
  simulador vetorizado. (`QAOAAnsatz` usa `PauliEvolutionGate`, menos transparente para métricas.)
- Simulador vetorizado próprio para o regime ideal: exato e ~10–100× mais barato que construir
  `Statevector` a cada avaliação; validado contra o Qiskit em teste. Ruído usa Aer.
- MILP linearizado em vez de MIQP: HiGHS não resolve MIQP; McCormick é exato para binários.
- Ruído avaliado por transferência (parâmetros otimizados no ideal, executados sob ruído) como protocolo
  principal: isola o efeito do ruído sobre o MESMO circuito. Otimização sob ruído fica fora do sweep.
- Um único `quantum/backends/` com 3 arquivos em vez de 5 (consolidação pedida na auditoria §6).
- Sem Dask/Ray/Streamlit (auditoria §11).

## Riscos

- `Fake27QPulseV1` é deprecated (removido no Qiskit 2.0) → isolado em `quantum/noise.py`, com fallback.
- Custo computacional dos sweeps → desenho em etapas e modo `--quick` para CI.
- Ruído com trajetórias é estocástico → seeds explícitas (`seed_simulator`, `seed_transpiler`).

## Plano de testes

T01–T18 da auditoria mapeados em `tests/test_*.py` (ver `tasks.md`). Testes de GPU com `skip`
explícito; QPU somente com mocks/injeção, nunca rede.
