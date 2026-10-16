# Comparação de MODELOS de risco (trilha `model_comparison`, medida — ver `python -m benchmarks.compare_methods`)

> Esta tabela NÃO ranqueia algoritmos: LP/MILP/estocástico/Benders otimizam retorno + *shortfall*;
> brute force e QAOA otimizam média-variância. Comparação de algoritmos no MESMO objetivo:
> `results/` (trilha `algorithm_benchmark`, `python -m benchmarks.fair_qubo_benchmark`).

Instância: ['PETR4', 'VALE3', 'ITUB4'], budget=2 · tempos de UMA execução, sem
distribuição estatística.

| Método | Tempo (s) | Selecionados | Obj. nativo | Risco quadrático | Shortfall esperado |
|---|---|---|---|---|---|
| Brute force (referência) | 0.0001 | VALE3, ITUB4 | 0.020500 | 0.020500 | 0.106425 |
| LP (relaxação linear) | 0.0037 | PETR4, VALE3 | 0.001063 | 0.028500 | 0.056126 |
| MILP (Pyomo + HiGHS) | 0.1518 | PETR4, VALE3 | 0.001063 | 0.028500 | 0.056126 |
| Estocástico 2 estágios (forma extensiva) | 0.0467 | PETR4, VALE3 | -0.011824 | 0.028500 | 0.056126 |
| Benders decomposition (2 iterações) | 0.0917 | PETR4, VALE3 | -0.011824 | 0.028500 | 0.056126 |
| QUBO/QAOA (simulação ideal sem ruído + 1024 shots amostrados) | 0.8432 | VALE3, ITUB4 | 0.020500 | 0.020500 | 0.106425 |

**Nota:** o QAOA usa `qiskit_algorithms.QAOA` com `StatevectorSampler` — o estado é calculado sem ruído e a saída são 1024 shots AMOSTRADOS dele (não são probabilidades exatas). Não há hardware quântico. Nesta instância de 3 qubits o QAOA reencontra o ótimo da busca exaustiva (mesmo objetivo média-variância); MILP/estocástico/Benders escolhem outra carteira porque otimizam OUTRO objetivo (shortfall), não por erro de nenhum dos lados. O QAOA é o método mais lento; nada aqui indica vantagem quântica.