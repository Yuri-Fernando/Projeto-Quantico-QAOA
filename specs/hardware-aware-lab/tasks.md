# Tasks — v0.3.0

## Epic A — Baseline e CI (P0)
- [ ] A01 Branch `feat/fair-qubo-benchmark` a partir de `c894c73`.
- [ ] A02 Arquivar saída do benchmark v0.2.0 e gerar lock das dependências testadas.
- [ ] A03 Problema canônico + `objective_id` + hash de instância (`canonical_qubo.py`).
- [ ] A04 MILP linearizado (McCormick, Pyomo/HiGHS) + relaxação LP do mesmo objetivo.
- [ ] A05 Testes de equivalência f/QUBO/Ising/MILP/enumeração (T01, T02, T18).
- [ ] A06 Separar trilha `model_comparison` × `algorithm_benchmark` (T17).
- [ ] A07 Corrigir README/benchmark: remover "QAOA == MILP" e "statevector exato".
- [ ] A08 Configs YAML, seeds e manifest por execução (T13).
- [ ] A09 CI (lint → testes → smoke offline → artefatos), pyproject.toml.

## Epic B — Engenharia do QAOA (P1)
- [ ] B01 Exportar QUBO, ρ, offset, Ising; teste da dupla contagem do legado.
- [ ] B02 Contagens, viabilidade, soluções inválidas (T03, T04).
- [ ] B03 p, otimizador (COBYLA/SPSA), inicialização, seed (T05, T06).
- [ ] B04 Mixer X + penalidade × mixer XY + Dicke.
- [ ] B05 Tempos por estágio, avaliações, métricas de circuito.
- [ ] B06 Sweep faseado com ICs (E1).

## Epic C — Ruído e conectividade (P1)
- [ ] C01 Backends ideal exato / Aer ideal / Aer ruidoso / fake.
- [ ] C02 Métricas pré/pós transpilation (T07, T08).
- [ ] C03 Readout e gate noise (E3).
- [ ] C04 Estudo de profundidade, 2Q, SWAPs e shots (E2).
- [ ] C05 Limitações do fake backend documentadas.

## Epic D — Híbrido CPU–GPU–QPU (P2)
- [ ] D01 Instrumentação de todos os estágios.
- [ ] D02 Adapter GPU com verificação real de disponibilidade.
- [ ] D03 Benchmark CPU × GPU — condicional a CUDA no Aer.
- [ ] D04 Adapter IBM QPU com opt-in e credenciais externas.
- [ ] D05 Limites de shots/jobs, timeout, metadados.
- [ ] D06 Mock/fake validando a interface (T09, T11, T14).
- [ ] D07 Microexperimento real — condicional a autorização e acesso.

## Epic E — Escala e caso industrial (P2/P3)
- [ ] E01 Gerador de instâncias n variáveis, PSD, seeds (T16).
- [ ] E02 Curvas de escala e limites de memória (E4).
- [ ] E03 Segundo caso: seleção de tarefas por turno com conflitos.
- [ ] E04 Clássico e QAOA com o mesmo objetivo no segundo caso.
- [ ] E05 Relatório científico com hipóteses, ICs, ameaças à validade.
- [ ] E06 Demo CLI/HTML e guia de capacitação.
