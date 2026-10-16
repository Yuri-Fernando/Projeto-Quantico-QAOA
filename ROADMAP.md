# Roadmap — Quantum–Classical Optimization & Hardware-Aware Benchmark Lab

Nada do plano anterior foi descartado — apenas resequenciado pela auditoria de 2026-10-15
(prioridade: comparação metodologicamente correta antes de hardware). Estado verificável em
`specs/hardware-aware-lab/tasks.md`.

## Fase 0 — Rascunho (concluída, ago/2025)
- [x] Toy problem de seleção de portfólio via QUBO+QAOA (preservado em `legacy/v1/`).

## Fase 1 — MVP comparativo de modelos (concluída, v0.2.0, 2026-10-07)
- [x] LP, MILP, estocástico de 2 estágios, Benders e QUBO/QAOA na mesma instância; 14 testes.
- [x] Reclassificada na v0.3.0 como trilha `model_comparison` (objetivos diferentes).

## Fase 2 — Benchmark justo e engenharia do QAOA (concluída, v0.3.0, 2026-10-15)
- [x] Problema canônico, QUBO/Ising auditáveis, MILP McCormick e heurísticas no MESMO objetivo (E0: 50/50).
- [x] Mixer X + penalidade × XY + Dicke; otimizadores, inicialização, shots, penalidade (E1, E1b, E1c).
- [x] Escala até n=20 em simulação (E4); segundo domínio industrial sintético (E7).

## Fase 3 — Hardware-aware em simulação (concluída, v0.3.0)
- [x] Transpilation para backends fake: SWAPs, portas 2Q, profundidade, layout, Target (E2).
- [x] Regimes de ruído e backends fake sob protocolo de transferência (E3).

## Fase 4 — Recursos reais (pendente de recurso externo)
- [ ] GPU: executar E5 num host Linux com `qiskit-aer-gpu` + CUDA (aqui o Aer é só CPU).
- [ ] QPU: instalar `qiskit-ibm-runtime`, credenciais fora do Git, rodar E6 com `--allow-qpu`
      (dry-run primeiro; job real só com orçamento autorizado).
- [ ] CI: primeira execução do workflow após push.

## Fase 5 — Próximos experimentos (planejada)
- [ ] Otimização variacional SOB ruído (não só transferência).
- [ ] Mitigação de erro (ex.: leitura) como experimento separado, com overhead medido.
- [ ] Mixers com menor custo de compilação (XY em pares paralelos, ordem compatível com a topologia).
- [ ] Penalidade adaptativa (ρ próximo do crítico estimado sem enumeração).
- [ ] Benders com master inteiro (trilha `model_comparison`).

## Depois / não priorizado (auditoria §11)
- [ ] SDDP/PDDE multiestágio.
- [ ] Paralelização (multiprocessing/Dask/Ray) — só após profiling indicar gargalo real.
- [ ] Port C++/OpenMP — idem.
- [ ] Interface web — depois de dados e estatística estáveis.
