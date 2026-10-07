# Scientific & Quantum Optimization Lab

**Stack:** Python 3.10 · NumPy · SciPy · Pyomo + HiGHS · OR-Tools · Qiskit (qiskit-optimization, qiskit-algorithms, qiskit-aer) · pytest

## Status

🟡 MVP funcional e testado (LP, MILP, estocástico de 2 estágios, Benders e QUBO/QAOA rodando na mesma instância, 14 testes passando), mas ainda de escala de brinquedo (3 ativos fictícios). SDDP/PDDE, HPC real (Dask/Ray) e C++/OpenMP ficaram explicitamente fora desta rodada — ver `ROADMAP.md`.

## Descrição

Este projeto evoluiu do rascunho `Projeto-Quantico-QAOA` (seleção de portfólio via QUBO+QAOA, ago/2025) para um laboratório comparativo de otimização matemática: o MESMO problema de seleção de portfólio é resolvido por cinco métodos diferentes — Programação Linear (LP), Programação Linear Inteira Mista (MILP), Programação Estocástica de 2 estágios com cenários, Decomposição de Benders, e QUBO/QAOA — permitindo comparar formulações, tempos de execução e qualidade de solução entre otimização clássica e quântica (simulada).

## Contexto

Parte da auditoria de portfólio de projetos (seção "Scientific Computing / Mathematical Optimization"), que recomendou evoluir o repo de QAOA isolado para um laboratório mais amplo cobrindo LP/MILP/estocástico/Benders/SDDP, com comparação honesta entre clássico e quântico. O rascunho original (`main.py` + `portfolio_qaoa.py`, preservados intactos na raiz como v1) usava uma API do Qiskit já desatualizada em agosto/2025 — ver "Bug real corrigido" abaixo.

## Objetivo

Demonstrar, de forma honesta e com números medidos (não prometidos), como diferentes paradigmas de otimização matemática — linear, inteira mista, estocástica, decomposição e quântica simulada — se comportam na MESMA instância de um problema real de alocação (seleção de portfólio), incluindo onde cada método vence, onde empata, e onde QAOA simulado não tem nenhuma vantagem.

## Linha de Pesquisa

Otimização matemática aplicada a finanças/alocação de recursos, com foco comparativo clássico vs quântico. Mesmo esqueleto de problema é reaproveitável para scheduling e energy dispatch (próximos passos, ver `ROADMAP.md`).

## Arquitetura

```
QAOA/
├── optimization/
│   ├── instance.py      # instância compartilhada (dados, 2 métricas de risco, brute force)
│   ├── lp.py             # LP: relaxação contínua (scipy.optimize.linprog, HiGHS)
│   ├── milp.py           # MILP: seleção binária real (Pyomo + HiGHS)
│   ├── stochastic.py     # estocástico 2 estágios, forma extensiva (Pyomo + HiGHS)
│   ├── benders.py        # decomposição de Benders real (loop de cortes, master+subproblemas)
│   └── qaoa.py           # QUBO/QAOA consertado (qiskit_algorithms + StatevectorSampler)
├── benchmarks/
│   ├── compare_methods.py  # roda os 5 métodos + brute force, mede tempo/objetivo/risco
│   └── results.md           # saída real da última execução (gerado, não escrito à mão)
├── tests/                  # 14 testes, cobrindo os 5 métodos + a instância compartilhada
├── main.py, portfolio_qaoa.py, *.ipynb   # v1 (rascunho original, preservado intacto)
├── requirements.txt        # pins novos e corretos (substitui requirements.txt.txt)
├── CHANGELOG.md / ROADMAP.md / WORKLOG.md
```

## Funcionamento

1. `optimization/instance.py` define a instância única: 3 ativos fictícios (PETR4, VALE3, ITUB4), retornos esperados e matriz de covariância (mesmos do rascunho v1), orçamento (escolher 2 de 3), e 8 cenários de retorno simulados (seed fixa, reprodutíveis) usados por LP/MILP/estocástico/Benders.
2. Cada módulo em `optimization/` resolve essa instância por um método diferente e devolve `{x, objective, ...}` no mesmo formato.
3. `benchmarks/compare_methods.py` roda todos os métodos, mede tempo real (`time.perf_counter`), e reavalia cada solução encontrada nas duas métricas de risco (ver "Modelagem") para comparação justa.
4. `tests/` valida corretude: relações de limite (LP ≤ MILP), convergência (Benders == forma extensiva monolítica), e correção absoluta (QAOA == busca exaustiva).

## Modelagem

Dois modelos de risco coexistem, por necessidade e documentado:

- **Risco quadrático (média-variância, `x^T Σ x`)** — nativo de QUBO/QAOA, que precisa de termos quadráticos. Usado por brute force e QAOA.
- **Risco de shortfall por cenário (linear, `E[max(0, τ − retorno)]`)** — necessário para que LP seja de fato um programa LINEAR (exigência da categoria). Usado por LP, MILP, estocástico e Benders.

Como os métodos otimizam objetivos formalmente diferentes, o benchmark reavalia TODAS as soluções finais nas DUAS métricas, para uma comparação honesta (ver `benchmarks/results.md`).

O estocástico de 2 estágios tem recurso real: depois de observar o retorno do cenário, pode-se comprar um hedge `y_s ∈ [0, hedge_cap]` a um custo por unidade, reduzindo o shortfall residual. A decomposição de Benders (L-shaped method) decompõe esse problema em um master (decide `x`) e um subproblema LP trivial por cenário, construindo cortes de otimalidade a partir dos multiplicadores duais — implementação real do loop, não um wrapper de solver.

## Experimental

- Instância: 3 ativos fictícios, budget=2, λ=0.5, 8 cenários (`seed=42`).
- QAOA: `reps=3`, otimizador COBYLA (`maxiter=250`), simulador `StatevectorSampler` (exato, sem shots, sem ruído).
- Todos os testes e o benchmark rodam localmente, sem hardware quântico real.

## Tecnologias

NumPy, SciPy (`linprog`, método HiGHS), Pyomo + `appsi_highs`, OR-Tools (instalado, não usado nesta rodada — ver Roadmap), Qiskit 1.4 + `qiskit-optimization` 0.7 + `qiskit-algorithms` 0.4 + `qiskit-aer` 0.17, pytest.

## Resultados

Última execução real de `python -m benchmarks.compare_methods` (ver `benchmarks/results.md` para a tabela completa gerada):

| Método | Tempo (s) | Selecionados | Risco quadrático | Shortfall esperado |
|---|---|---|---|---|
| Brute force | 0.0001 | VALE3, ITUB4 | 0.0205 | 0.1064 |
| LP (relaxação) | 0.0045 | PETR4, VALE3 | 0.0285 | 0.0561 |
| MILP | 0.1893 | PETR4, VALE3 | 0.0285 | 0.0561 |
| Estocástico (extensivo) | 0.0342 | PETR4, VALE3 | 0.0285 | 0.0561 |
| Benders (2 iterações) | 0.0715 | PETR4, VALE3 | 0.0285 | 0.0561 |
| QUBO/QAOA (statevector) | 1.4095 | VALE3, ITUB4 | 0.0205 | 0.1064 |

**Achado real:** LP/MILP/estocástico/Benders convergem todos para a mesma carteira (PETR4+VALE3, ótima pela métrica de shortfall), enquanto QAOA e a busca exaustiva convergem para VALE3+ITUB4 (ótima pela métrica quadrática média-variância) — ou seja, os dois grupos de métodos não estão "errados" um em relação ao outro; estão otimizando riscos diferentes por construção. QAOA foi, como esperado, o método mais lento (simulação estatevector local, sem nenhuma vantagem quântica real nesta escala de 3 qubits).

**Bug real corrigido:** a API do rascunho v1 (`from qiskit.algorithms import QAOA`, `qiskit.primitives.Estimator`) não funciona mais — `qiskit.algorithms.QAOA` foi removido em Qiskit ≥1.0 (migrou para o pacote `qiskit_algorithms`), e o primitive V1 `Estimator`/`Sampler` é incompatível com a pipeline interna atual (gera `TypeError: Invalid circuits, expected Sequence[QuantumCircuit]`). Corrigido usando `qiskit_algorithms.QAOA` + `qiskit.primitives.StatevectorSampler` (V2). O ambiente também tinha Qiskit <1.0 e ≥1.0 misturados simultaneamente (`ImportError: Qiskit is installed in an invalid environment...`), resolvido reinstalando um conjunto de versões consistente (ver `requirements.txt`).

## Roadmap

Ver `ROADMAP.md`.

## Próximos Passos

- SDDP/PDDE para o estocástico multiestágio (fora de escopo nesta rodada).
- HPC/paralelização real dos cenários (Dask/Ray) — `multiprocessing` padrão não foi necessário na escala atual (8 cenários, resolvido em milissegundos).
- Port de componentes críticos para C++/OpenMP.
- Expandir a instância para mais ativos e comparar escalabilidade de cada método.
