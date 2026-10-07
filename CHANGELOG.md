# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e [SemVer](https://semver.org/lang/pt-BR/).

## [0.2.0] - 2026-10-07

### Adicionado
- `optimization/instance.py`: instância compartilhada do problema de portfólio (3 ativos fictícios, 8 cenários reprodutíveis, duas métricas de risco — quadrática e shortfall por cenário).
- `optimization/lp.py`: relaxação linear contínua via `scipy.optimize.linprog` (HiGHS).
- `optimization/milp.py`: formulação MILP (seleção binária real) via Pyomo + `appsi_highs`.
- `optimization/stochastic.py`: programa estocástico de 2 estágios com recurso (hedge por cenário), forma extensiva via Pyomo + HiGHS.
- `optimization/benders.py`: decomposição de Benders real (L-shaped method), loop de master + subproblemas por cenário com cortes de otimalidade construídos a partir de duais.
- `optimization/qaoa.py`: QUBO/QAOA reescrito sobre a instância compartilhada, com restrição de orçamento nativa (não penalidade manual).
- `benchmarks/compare_methods.py`: benchmark real medindo tempo e qualidade de solução (duas métricas) dos 5 métodos + busca exaustiva.
- `tests/`: 14 testes cobrindo os 5 métodos e a instância (relações de limite LP≤MILP, convergência Benders≈estocástico monolítico, QAOA==brute force).
- `requirements.txt`, `.gitignore`, `conftest.py`.
- `README.md`, `ROADMAP.md`, `WORKLOG.md`.

### Corrigido
- API desatualizada do Qiskit no rascunho original (`qiskit.algorithms.QAOA`, removido em Qiskit ≥1.0; `qiskit.primitives.Estimator`/`Sampler` V1 incompatível com a pipeline interna de `qiskit_algorithms` nesta versão). Corrigido com `qiskit_algorithms.QAOA` + `qiskit.primitives.StatevectorSampler`.
- Ambiente Python com Qiskit <1.0 e ≥1.0 instalados simultaneamente (conflito de dependências transitivo causado por `pip install qiskit-algorithms`), causando `ImportError` na importação de `qiskit`. Resolvido com reinstalação limpa de um conjunto de versões consistente.

### Não alterado (preservado como v1)
- `main.py`, `portfolio_qaoa.py`, `qaoa_portfolio.ipynb`, `qaoa_portfolio1.ipynb`, `requirements.txt.txt` — rascunho original intacto, não sobrescrito.

## [0.1.0] - 2025-08-20

### Adicionado
- Rascunho inicial: seleção de portfólio (PETR4/VALE3/ITUB4) via QUBO+QAOA, usando `qiskit-optimization`/`qiskit-aer` (`main.py`, `portfolio_qaoa.py`, notebooks).
