# Tasks — v0.3.0

Legenda: `[x]` implementado + testado + executado · `[~]` implementado e testado com mocks/skip, execução
real bloqueada por recurso externo · `[ ]` não feito.

## Epic A — Baseline e CI (P0)
- [x] A01 Branch `feat/fair-qubo-benchmark` a partir de `c894c73`.
- [x] A02 Saída do benchmark v0.2.0 arquivada + lock do ambiente (`benchmarks/archive/v0.2.0/`).
- [x] A03 Problema canônico + `objective_id` + hash de instância (`canonical_qubo.py`).
- [x] A04 MILP linearizado (McCormick, Pyomo/HiGHS) + relaxação LP do mesmo objetivo.
- [x] A05 Testes de equivalência f/QUBO/Ising/MILP/enumeração (T01, T02, T18) + E0 (50/50).
- [x] A06 Trilhas `model_comparison` × `algorithm_benchmark` separadas (T17).
- [x] A07 README/benchmark sem "QAOA == MILP" e sem "statevector exato".
- [x] A08 Configs YAML, seeds e manifest por execução (T13).
- [~] A09 CI escrito (`.github/workflows/ci.yml`); só roda após push — não executado nesta revisão.

## Epic B — Engenharia do QAOA (P1)
- [x] B01 QUBO, ρ, offset e Ising exportados; dupla contagem do legado confirmada por teste.
- [x] B02 Contagens, viabilidade, soluções inválidas (T03, T04).
- [x] B03 p, otimizador (COBYLA/SPSA), inicialização, seed (T05, T06; E1b).
- [x] B04 Mixer X + penalidade × mixer XY + Dicke (E1, E7).
- [x] B05 Tempos por estágio, avaliações, métricas de circuito.
- [x] B06 Sweep faseado com ICs (E1: 5 tamanhos × 4 profundidades × 10 seeds × 3 instâncias).

## Epic C — Ruído e conectividade (P1)
- [x] C01 Backends ideal exato / Aer ideal / Aer ruidoso / fake.
- [x] C02 Métricas pré/pós transpilation (T07, T08; E2).
- [x] C03 Readout e gate noise (E3).
- [x] C04 Profundidade, 2Q, SWAPs e shots (E2, E1b).
- [x] C05 Limitações do fake backend (`docs/HARDWARE_LIMITATIONS.md`).

## Epic D — Híbrido CPU–GPU–QPU (P2)
- [x] D01 Instrumentação de todos os estágios (`hpc/orchestrator.py`).
- [x] D02 Adapter GPU com verificação real de disponibilidade.
- [~] D03 CPU × GPU — GPU existe no host mas o qiskit-aer instalado é só CPU; E5 registra `not_executed`.
- [~] D04 Adapter IBM QPU com opt-in e credenciais externas — `BLOCKED_BY_CONFIGURATION`.
- [x] D05 Limites de shots/jobs, timeout, metadados (testados com mocks).
- [x] D06 Mock/fake validando a interface (T09, T11, T14).
- [ ] D07 Microexperimento real — depende de autorização, cota e credenciais do proprietário.

## Epic E — Escala e caso industrial (P2/P3)
- [x] E01 Gerador de instâncias n variáveis, PSD, seeds (T16).
- [x] E02 Curvas de escala e limites de memória (E4).
- [x] E03 Segundo caso: seleção de tarefas por turno com conflitos.
- [x] E04 Clássico e QAOA com o mesmo objetivo no segundo caso (E7).
- [x] E05 Relatório técnico (`docs/SCIENTIFIC_RESULTS.md`).
- [x] E06 Demo CLI/HTML (`experiments/demo.py`) e guia de capacitação (`docs/TRAINING_GUIDE.md`).
