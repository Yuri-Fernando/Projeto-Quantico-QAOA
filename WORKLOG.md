# Worklog — sessão de implementação (2026-10-07)

Item #2 de prioridade da auditoria de portfólio (depois do ArgusAI, já concluído). Objetivo: evoluir `Projeto-Quantico-QAOA` para "Scientific & Quantum Optimization Lab", implementando LP/MILP/estocástico/Benders/QUBO-QAOA sobre o mesmo problema, com testes e histórico git.

## Estado inicial

- Git acabado de inicializar (`git init`), commit baseline `5613f5a` com os arquivos soltos do rascunho (`main.py`, `portfolio_qaoa.py`, notebooks, `requirements.txt.txt`).
- `git status` limpo confirmado antes de começar.
- Python canônico: `C:\Users\Yuri_\AppData\Local\Programs\Python\Python310\python.exe` (3.10.8).

## Diagnóstico do ambiente

- `pip list` mostrou `qiskit 0.43.3` + `qiskit-terra 0.24.2` + `qiskit-ibmq-provider 0.20.2` (API antiga, pré-1.0) e NENHUM `pyomo`/`highspy` instalado. `ortools` já estava presente.
- Tentei `from qiskit.algorithms import QAOA` (import original do rascunho) isoladamente: falhou com `ImportError: Qiskit is installed in an invalid environment...` mesmo ANTES de qualquer alteração minha — ambiente já estava inconsistente.
- `pip install pyomo highspy qiskit-algorithms` puxou `qiskit 2.5.2` como dependência transitiva de `qiskit-algorithms`, piorando o conflito (qiskit 0.43 old-style + 2.5.2 coexistindo).
- Correção: `pip uninstall qiskit-terra qiskit-ibmq-provider qiskit-aer qiskit-optimization qiskit`, depois `pip install "qiskit>=1.0,<2.0" qiskit-aer qiskit-optimization qiskit-algorithms` → resolveu para `qiskit 1.4.6`, `qiskit-aer 0.17.2`, `qiskit-optimization 0.7.0`, `qiskit-algorithms 0.4.0` (conjunto consistente).

## Bug de API do Qiskit (confirmado e corrigido)

- Com o ambiente limpo, testei `QAOA(sampler=Sampler(), ...)` (primitive V1): falhou em runtime com `TypeError: Invalid circuits, expected Sequence[QuantumCircuit]` dentro de `qiskit_algorithms...diagonal_estimator.py` — incompatibilidade entre o primitive V1 `Sampler` e a pipeline interna do `SamplingVQE`/`QAOA` nesta combinação de versões.
- Troquei para `StatevectorSampler` (primitive V2): funcionou imediatamente, confirmado com um teste mínimo de 2 variáveis binárias antes de integrar ao projeto real.

## Implementação

1. `optimization/instance.py` — instância compartilhada, dois modelos de risco (quadrático para QUBO/QAOA, shortfall-por-cenário linear para LP/MILP/estocástico/Benders), busca exaustiva para validação.
2. `optimization/lp.py` — LP via `scipy.optimize.linprog` (método HiGHS).
3. `optimization/milp.py` — MILP via Pyomo + `appsi_highs`.
4. `optimization/stochastic.py` — forma extensiva do estocástico de 2 estágios com recurso real (hedge por cenário, trade-off de custo).
5. `optimization/benders.py` — decomposição de Benders implementada do zero (master Pyomo + subproblemas `scipy.linprog` por cenário, cortes construídos a partir dos multiplicadores duais retornados por `res.ineqlin.marginals`). Validado manualmente antes dos testes formais: convergiu em 2 iterações, diferença de ~1.7e-18 contra a forma extensiva monolítica relaxada.
6. `optimization/qaoa.py` — QUBO/QAOA reescrito com a API corrigida, restrição de orçamento como restrição linear nativa do `QuadraticProgram` (não penalidade manual como no v1).
7. `benchmarks/compare_methods.py` — roda os 5 métodos + brute force, mede tempo real, reavalia cada solução nas duas métricas de risco.
8. `tests/` — 14 testes (instância, LP, MILP, estocástico, Benders, QAOA).

## Validação

- `pytest -v`: **14 passed** (30.19s), 1 warning (PendingDeprecationWarning interno do Qiskit sobre `NLocal`, não relacionado ao nosso código).
- `python -m benchmarks.compare_methods`: executado com sucesso, resultados reais salvos em `benchmarks/results.md` e `benchmarks/results.json`.
- Achado real do benchmark: LP/MILP/estocástico/Benders convergem para a carteira PETR4+VALE3 (ótima por shortfall), enquanto QAOA e busca exaustiva convergem para VALE3+ITUB4 (ótima por risco quadrático) — resultado esperado e documentado no README, não um bug: os dois grupos otimizam riscos diferentes por construção.
- QAOA foi o método mais lento (~1.4s, simulação estatevector local) — nenhuma vantagem quântica fingida; documentado explicitamente.

## Fora de escopo (documentado no ROADMAP.md)

- SDDP/PDDE, HPC/paralelização real (Dask/Ray), port C++/OpenMP, hardware quântico real.

## Commits

Ver `git log` — commits incrementais em português (`feat:`/`docs:`/`chore:`), sem `git push`.
