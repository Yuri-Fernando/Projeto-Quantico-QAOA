# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e [SemVer](https://semver.org/lang/pt-BR/).

## [0.3.0] - 2026-10-15

Implementação da auditoria técnica de 2026-10-15 (benchmark de mesmo objetivo, QAOA instrumentado,
hardware-aware, ruído, CPU/GPU/QPU com guardas, escala, segundo domínio, reprodutibilidade).

### Adicionado
- `optimization/canonical_qubo.py`: problema canônico com `objective_id`/hash, QUBO penalizado com ρ
  exportado, penalidade segura (com prova) e crítica, Ising e `SparsePauliOp` com ordem de bits documentada.
- `optimization/classical_qubo.py`: enumeração, MILP linearizado (McCormick/HiGHS) e relaxação LP do
  MESMO objetivo do QAOA; `optimization/heuristics.py`: simulated annealing e amostragem aleatória viável.
- `optimization/instance.py`: validação (PSD, simetria, k, probabilidades) e gerador de instâncias de n
  ativos; `optimization/scheduling.py`: segundo domínio (seleção de tarefas por turno com conflitos).
- `quantum/`: circuito QAOA explícito (mixer X + penalidade; mixer XY em anel + estado de Dicke),
  simulador exato vetorizado, runner (COBYLA/SPSA, inicializações, modo exato/amostrado), medição e
  estatística (viabilidade, P(ótimo), Wilson, bootstrap), transpilation hardware-aware (SWAPs, layout,
  Target), regimes de ruído e backends fake, `ExecutionResult` unificado, adaptadores Aer CPU/GPU e IBM QPU.
- `hpc/`: detecção real de dispositivos, profiling e orquestrador híbrido com tempos por estágio.
- `experiments/`: CLI por YAML (E0–E7), manifest por execução, análise que regenera tabelas/figuras só de
  dados salvos, demonstrador HTML de 5 passos.
- `results/`: execuções oficiais de E0–E7 com manifests, registros e contagens brutas.
- Documentação: formulação, protocolo, arquitetura, limitações de hardware, relatório técnico, ADR-001,
  guia de capacitação, template de relatório; `specs/hardware-aware-lab/`.
- `pyproject.toml`, `requirements-lock.txt`, `tools/lock_deps.py`, `.github/workflows/ci.yml`.
- 166 testes novos (suíte: 180 coletados, 179 passam, 1 skip explícito de GPU; os 14 da v0.2.0 inalterados).

### Corrigido
- Benchmark de modelos rotulava a simulação como "statevector exato" e afirmava que o QAOA encontrava o
  mesmo ótimo do MILP — objetivos diferentes. Agora é a trilha `model_comparison`, com nota explícita.
- Contorno para `IndexError` do Qiskit 1.4.6 em `Layout.initial_index_layout(filter_ancillas=True)`.
- Hash de modelo de ruído estável (remove `id` aleatório de `NoiseModel.to_dict()`).

### Confirmado (sem alteração do arquivo)
- Dupla contagem do termo cruzado da penalidade em `legacy/v1/portfolio_qaoa.py::build_qubo`
  (diferença exata `2ρ Σ_{i<j} x_i x_j`, `tests/test_legacy_penalty.py`).

### Alterado
- Rascunho v1 movido para `legacy/v1/` com `git mv` (conteúdo intacto); saída do benchmark v0.2.0
  arquivada em `benchmarks/archive/v0.2.0/`.
- `requirements.txt`: + `pyyaml`, + `ruff`; − `ortools` (nunca importado).

### Removido do versionamento
- Arquivo de notas pessoais do rascunho v1 (`projeto quântico.txt`): deixou de ser rastreado e entrou
  no `.gitignore`. A parte técnica foi preservada em `legacy/v1/notas_tecnicas_v1.md`. O arquivo
  continua presente nos commits anteriores do histórico.

### Não executado (bloqueado por recurso externo)
- GPU: `qiskit-aer` instalado é só CPU (`available_devices() == ('CPU',)`).
- QPU IBM: `qiskit-ibm-runtime` e credenciais ausentes; adaptador testado só com mocks.
- CI: workflow escrito, executa após push.

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
