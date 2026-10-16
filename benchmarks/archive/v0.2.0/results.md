# Resultados do benchmark (medidos — ver `python -m benchmarks.compare_methods`)

Instância: ['PETR4', 'VALE3', 'ITUB4'], budget=2

| Método | Tempo (s) | Selecionados | Obj. nativo | Risco quadrático | Shortfall esperado |
|---|---|---|---|---|---|
| Brute force (referência) | 0.0001 | VALE3, ITUB4 | 0.020500 | 0.020500 | 0.106425 |
| LP (relaxação linear) | 0.0045 | PETR4, VALE3 | 0.001063 | 0.028500 | 0.056126 |
| MILP (Pyomo + HiGHS) | 0.1893 | PETR4, VALE3 | 0.001063 | 0.028500 | 0.056126 |
| Estocástico 2 estágios (forma extensiva) | 0.0342 | PETR4, VALE3 | -0.011824 | 0.028500 | 0.056126 |
| Benders decomposition (2 iterações) | 0.0715 | PETR4, VALE3 | -0.011824 | 0.028500 | 0.056126 |
| QUBO/QAOA (simulado, statevector exato) | 1.4095 | VALE3, ITUB4 | 0.020500 | 0.020500 | 0.106425 |

**Nota honesta:** o QAOA aqui roda em simulador estatevector local (sem ruído, sem hardware quântico real). Ele NÃO tem nenhuma vantagem de tempo sobre os métodos clássicos nesta instância de 3 qubits — pelo contrário, é o método mais lento do benchmark. O objetivo desta comparação é validar CORREÇÃO (QAOA encontra o mesmo ótimo que busca exaustiva / MILP), não demonstrar vantagem quântica, que não existe nesta escala nem nesta configuração.