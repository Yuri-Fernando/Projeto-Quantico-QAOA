# Roadmap — Scientific & Quantum Optimization Lab

Nada do plano original da auditoria é descartado aqui — apenas sequenciado. Itens fora de escopo desta rodada ficam explicitamente marcados como "depois".

## Fase 0 — Rascunho (concluída, ago/2025)

- [x] Toy problem de seleção de portfólio via QUBO+QAOA (v1, preservado intacto).

## Fase 1 — MVP comparativo clássico vs quântico (concluída, 2026-10-07)

- [x] Instância compartilhada (`optimization/instance.py`) com duas métricas de risco.
- [x] LP (relaxação linear, `scipy.optimize.linprog`).
- [x] MILP (Pyomo + HiGHS).
- [x] Programação estocástica de 2 estágios com cenários e recurso real (forma extensiva).
- [x] Decomposição de Benders real (loop de cortes, não wrapper de solver).
- [x] QUBO/QAOA consertado (API do Qiskit atualizada) e integrado à mesma instância.
- [x] Benchmark real (`benchmarks/compare_methods.py`) com números medidos.
- [x] 14 testes cobrindo os 5 métodos.

## Fase 2 — Escala e robustez (próxima)

- [ ] Expandir a instância para mais ativos (ex.: 6–10) e medir como cada método escala.
- [ ] Adicionar um segundo problema do mesmo "esqueleto" (scheduling ou energy dispatch) resolvido pelos mesmos 5 métodos, para generalizar a comparação além de portfólio.
- [ ] Benders com master inteiro (branch-and-cut com cortes de Benders, não apenas relaxação contínua).
- [ ] Explorar CVXPY e/ou Julia-JuMP como alternativa de modelagem (opcional, mencionado na auditoria).

## Fase 3 — SDDP/PDDE (depois, fora de escopo nesta rodada)

- [ ] Programação dinâmica estocástica dual (SDDP) para o problema multiestágio (a versão atual é de 2 estágios apenas).
- [ ] Comparar SDDP vs Benders de 2 estágios vs forma extensiva em termos de escalabilidade.

## Fase 4 — HPC / paralelização real (depois, fora de escopo nesta rodada)

- [ ] Paralelizar a resolução dos subproblemas de Benders por cenário com `multiprocessing`, Dask ou Ray (não foi necessário na escala atual — 8 cenários resolvem em milissegundos).
- [ ] Profiling real (cProfile/line_profiler) nos métodos antes de qualquer paralelização, para evitar otimização prematura.

## Fase 5 — Port para C++/OpenMP (depois, fora de escopo nesta rodada)

- [ ] Identificar o(s) subproblema(s) mais custosos computacionalmente em escala maior.
- [ ] Portar apenas esses trechos para C++ com OpenMP, mantendo a API Python como camada de orquestração.

## Fase 6 — Hardware quântico real (depois, não comprometido)

- [ ] Rodar o mesmo QUBO em um backend real via IBM Quantum (ou simulador com ruído), documentando honestamente overhead de fila, erro de hardware e qualquer (não-)vantagem observada.
