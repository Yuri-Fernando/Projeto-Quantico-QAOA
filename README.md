# 🔬 Scientific & Quantum Optimization Lab — o mesmo problema, cinco métodos de otimização

### Python 3.10 · NumPy · SciPy · Pyomo + HiGHS · OR-Tools · Qiskit (qiskit-optimization/algorithms/aer) · pytest

![testes](https://img.shields.io/badge/pytest-14%20passed-0a8a0a)
![benchmark](https://img.shields.io/badge/benchmark-5%20m%C3%A9todos%20comparados-2a78d6)
![versão](https://img.shields.io/badge/vers%C3%A3o-v0.2.0-4a5563) ![licença](https://img.shields.io/badge/licen%C3%A7a-n%C3%A3o%20definida-4a5563)

---

## Status

🟡 **MVP técnico funcional** — LP, MILP, programação estocástica de 2 estágios, decomposição de
Benders e QUBO/QAOA rodando sobre a MESMA instância de um problema de seleção de portfólio, com 14
testes passando (`pytest -v`, 30,19s) e um benchmark real medido (`benchmarks/results.md`). Ainda de
**escala de brinquedo** (3 ativos fictícios, 8 cenários). SDDP/PDDE, HPC real (Dask/Ray), port
C++/OpenMP e hardware quântico real ficaram explicitamente fora desta rodada — ver
[`ROADMAP.md`](ROADMAP.md).

---

## Descrição / Contexto

Este projeto evoluiu do rascunho `Projeto-Quantico-QAOA` (seleção de portfólio via QUBO+QAOA,
agosto/2025) para um laboratório comparativo de otimização matemática: o MESMO problema de seleção de
portfólio é resolvido por cinco métodos diferentes — **Programação Linear (LP)**, **Programação
Linear Inteira Mista (MILP)**, **Programação Estocástica de 2 estágios com cenários**,
**Decomposição de Benders** e **QUBO/QAOA** — permitindo comparar formulações, tempos de execução e
qualidade de solução entre otimização clássica e otimização quântica simulada.

O rascunho original (`main.py` + `portfolio_qaoa.py` + notebooks, preservados intactos na raiz como
v1 — ver [Evidências](#️-evidências)) usava uma API do Qiskit já desatualizada em agosto/2025. A
primeira tarefa desta rodada foi diagnosticar e corrigir esse código antes de expandir o escopo — ver
[Desenvolvimento Experimental](#-desenvolvimento-experimental).

---

## 🧭 Origem do Projeto

Item de prioridade #2 de uma auditoria de portfólio pessoal (depois do `ArgusAI`, já concluído na
mesma rodada), que recomendou evoluir o repositório de QAOA isolado para um laboratório mais amplo
cobrindo LP/MILP/estocástico/Benders/SDDP, com comparação honesta entre otimização clássica e
quântica, em vez de um único script QUBO+QAOA sem contraponto. Sequência real desta sessão:

1. **Diagnóstico do ambiente** — `pip list` revelou `qiskit 0.43.3` (API pré-1.0) sem `pyomo`/
   `highspy` instalados; o import original do rascunho (`from qiskit.algorithms import QAOA`) já
   falhava mesmo antes de qualquer alteração.
2. **Correção do ambiente** — reinstalação limpa (`qiskit>=1.0,<2.0` + `qiskit-aer` + `qiskit-optimization`
   + `qiskit-algorithms`) para eliminar o conflito entre Qiskit <1.0 e ≥1.0 coexistindo.
3. **Correção da API** — `qiskit.algorithms.QAOA` foi removido em Qiskit ≥1.0 (migrou para
   `qiskit_algorithms`); o primitive V1 `Sampler`/`Estimator` é incompatível com a pipeline interna
   desta combinação de versões — resolvido com `qiskit_algorithms.QAOA` + `StatevectorSampler` (V2).
4. **Implementação dos 4 métodos clássicos** sobre uma instância compartilhada, não isolados —
   condição para a comparação ser honesta.
5. **Benchmark e 14 testes**, cobrindo relações de limite, convergência entre métodos e correção
   absoluta do QAOA contra busca exaustiva.

Nada do plano original da auditoria foi descartado — apenas sequenciado; os itens fora de escopo
desta rodada (SDDP, HPC, C++, hardware quântico real) estão explicitamente marcados "depois" em
[`ROADMAP.md`](ROADMAP.md).

---

## 🎯 Objetivo

Demonstrar, de forma honesta e com números medidos (não prometidos), como diferentes paradigmas de
otimização matemática — linear, inteira mista, estocástica, decomposição e quântica simulada — se
comportam na MESMA instância de um problema real de alocação (seleção de portfólio), incluindo onde
cada método vence, onde empata, e onde o QAOA simulado não tem nenhuma vantagem.

- Resolver o mesmo problema de seleção de portfólio por 5 formulações diferentes, sobre a mesma
  instância de dados;
- Medir tempo de execução e qualidade de solução de cada método de forma comparável (reavaliação
  cruzada nas duas métricas de risco);
- Implementar uma decomposição de Benders real (loop de cortes a partir de duais), não um wrapper de
  solver;
- Corrigir e validar o QUBO/QAOA original contra uma API atual do Qiskit, com restrição de orçamento
  nativa (não penalidade manual);
- Documentar honestamente onde o QAOA simulado não tem vantagem nenhuma sobre os métodos clássicos
  nesta escala.

---

## 🔬 Linha de Pesquisa / Desenvolvimento

Otimização matemática aplicada a finanças/alocação de recursos, com foco comparativo clássico vs.
quântico simulado: programação linear e inteira mista, programação estocástica com recurso,
decomposição de Benders (L-shaped method) e QUBO/QAOA sobre simulador estatevector exato. O mesmo
"esqueleto" de problema (instância + 2 métricas de risco + 5 solvers) é pensado para ser reaproveitado
em scheduling e energy dispatch — ver [Roadmap](#️-roadmap).

---

## 🏗️ Arquitetura

```text
QAOA/
├── optimization/
│   ├── instance.py      # instância compartilhada (dados, 2 métricas de risco, busca exaustiva)
│   ├── lp.py             # LP: relaxação contínua (scipy.optimize.linprog, HiGHS)
│   ├── milp.py           # MILP: seleção binária real (Pyomo + HiGHS)
│   ├── stochastic.py     # estocástico 2 estágios, forma extensiva (Pyomo + HiGHS)
│   ├── benders.py        # decomposição de Benders real (loop de cortes, master+subproblemas)
│   └── qaoa.py           # QUBO/QAOA consertado (qiskit_algorithms + StatevectorSampler)
├── benchmarks/
│   ├── compare_methods.py  # roda os 5 métodos + brute force, mede tempo/objetivo/risco
│   ├── results.md           # saída real da última execução (gerado, não escrito à mão)
│   └── results.json          # mesma saída em formato máquina-legível
├── tests/                  # 14 testes, cobrindo os 5 métodos + a instância compartilhada
├── main.py, portfolio_qaoa.py, *.ipynb   # v1 (rascunho original, preservado intacto)
├── requirements.txt        # pins novos e corretos (substitui requirements.txt.txt)
└── CHANGELOG.md / ROADMAP.md / WORKLOG.md
```

### Módulos

| Módulo | Função | Teste |
|---|---|---|
| `optimization/instance.py` | Instância compartilhada: 3 ativos fictícios, 8 cenários reprodutíveis (seed fixa), 2 métricas de risco, busca exaustiva de referência | `tests/test_instance.py` |
| `optimization/lp.py` | LP — relaxação contínua via `scipy.optimize.linprog` (HiGHS) | `tests/test_lp.py` |
| `optimization/milp.py` | MILP — seleção binária real via Pyomo + `appsi_highs` | `tests/test_milp.py` |
| `optimization/stochastic.py` | Estocástico de 2 estágios, forma extensiva, recurso real (hedge por cenário) | `tests/test_stochastic.py` |
| `optimization/benders.py` | Decomposição de Benders (L-shaped) — master Pyomo + subproblemas `scipy.linprog` por cenário, cortes a partir de duais | `tests/test_benders.py` |
| `optimization/qaoa.py` | QUBO/QAOA sobre a mesma instância, orçamento como restrição linear nativa | `tests/test_qaoa.py` |
| `benchmarks/compare_methods.py` | Roda os 5 métodos + brute force, mede tempo real, reavalia nas 2 métricas | `tests/test_benders.py` (convergência cruzada) |

---

## ⚙️ Funcionamento

1. `optimization/instance.py` define a instância única: 3 ativos fictícios (PETR4, VALE3, ITUB4),
   retornos esperados e matriz de covariância, orçamento (escolher 2 de 3), e 8 cenários de retorno
   simulados (seed fixa, reprodutíveis) usados por LP/MILP/estocástico/Benders.
2. Cada módulo em `optimization/` resolve essa instância por um método diferente e devolve
   `{x, objective, ...}` no mesmo formato.
3. `benchmarks/compare_methods.py` roda todos os métodos, mede tempo real (`time.perf_counter`), e
   reavalia cada solução encontrada nas duas métricas de risco (ver "Verificação / Modelagem") para
   comparação justa.
4. `tests/` valida corretude: relações de limite (LP ≤ MILP), convergência (Benders ≈ forma extensiva
   monolítica), e correção absoluta (QAOA == busca exaustiva).

Fluxo ponta a ponta:

```text
instance.py (dados + 2 métricas de risco)
        │
        ├──► lp.py ──────────┐
        ├──► milp.py ────────┤
        ├──► stochastic.py ──┼──► compare_methods.py ──► results.md / results.json
        ├──► benders.py ─────┤         (tempo real + reavaliação cruzada)
        └──► qaoa.py ────────┘
```

---

## 🧠 Verificação / Modelagem

Dois modelos de risco coexistem, por necessidade e documentado:

| Modelo de risco | Natureza | Usado por |
|---|---|---|
| Quadrático (média-variância, `x^T Σ x`) | Nativo de QUBO/QAOA, que precisa de termos quadráticos | Brute force (oráculo), QAOA |
| Shortfall por cenário (linear, `E[max(0, τ − retorno)]`) | Necessário para LP ser de fato um programa LINEAR | LP, MILP, estocástico, Benders |

Como os métodos otimizam objetivos formalmente diferentes, o benchmark reavalia TODAS as soluções
finais nas DUAS métricas, para uma comparação honesta (ver `benchmarks/results.md`).

O oráculo de correção é **busca exaustiva** (`instance.py`), independente de qualquer solver — o
teste `QAOA == busca exaustiva` valida o QAOA contra esse oráculo, não contra o resultado esperado de
outro método heurístico. O estocástico de 2 estágios tem recurso real: depois de observar o retorno do
cenário, pode-se comprar um hedge `y_s ∈ [0, hedge_cap]` a um custo por unidade, reduzindo o shortfall
residual. A decomposição de Benders (L-shaped method) decompõe esse problema em um master (decide `x`)
e um subproblema LP trivial por cenário, construindo cortes de otimalidade a partir dos multiplicadores
duais — implementação real do loop, não um wrapper de solver; validado manualmente antes dos testes
formais: convergiu em 2 iterações, diferença de ~1,7e-18 contra a forma extensiva monolítica relaxada.

---

## 🧪 Desenvolvimento Experimental

Achados reais desta sessão, não plantados:

1. **Ambiente já estava quebrado antes de qualquer alteração.** `from qiskit.algorithms import QAOA`
   (import original do rascunho v1) falhava com `ImportError: Qiskit is installed in an invalid
   environment...` mesmo antes de qualquer mudança — `pip list` mostrou `qiskit 0.43.3` +
   `qiskit-terra 0.24.2` (API pré-1.0), sem `pyomo`/`highspy` instalados.
2. **Instalar as dependências novas piorou o conflito antes de corrigi-lo.** `pip install pyomo
   highspy qiskit-algorithms` puxou `qiskit 2.5.2` como dependência transitiva de
   `qiskit-algorithms`, deixando `qiskit 0.43` (old-style) e `2.5.2` coexistindo. Corrigido com
   desinstalação completa (`qiskit-terra`, `qiskit-ibmq-provider`, `qiskit-aer`,
   `qiskit-optimization`, `qiskit`) e reinstalação pinada em `qiskit>=1.0,<2.0`.
3. **Bug de API confirmado e corrigido.** Com o ambiente limpo, `QAOA(sampler=Sampler(), ...)`
   (primitive V1) falhava em runtime com `TypeError: Invalid circuits, expected
   Sequence[QuantumCircuit]` dentro de `qiskit_algorithms...diagonal_estimator.py` — incompatibilidade
   entre o primitive V1 `Sampler` e a pipeline interna de `SamplingVQE`/`QAOA` nesta combinação de
   versões. Trocar para `StatevectorSampler` (primitive V2) resolveu imediatamente, confirmado com um
   teste mínimo de 2 variáveis binárias antes de integrar ao projeto real.
4. **Benders validado manualmente antes dos testes formais** — convergiu em 2 iterações, diferença de
   ~1,7e-18 contra a forma extensiva monolítica relaxada (não é uma aproximação grosseira, é
   numericamente idêntica dentro da tolerância de ponto flutuante).
5. **Achado honesto do benchmark**: LP/MILP/estocástico/Benders convergem para a carteira
   PETR4+VALE3 (ótima por shortfall), enquanto QAOA e busca exaustiva convergem para VALE3+ITUB4
   (ótima por risco quadrático) — resultado esperado e documentado, não um bug: os dois grupos
   otimizam riscos diferentes por construção (ver "Resultados").
6. **QAOA foi o método mais lento do benchmark** (~1,41s, simulação estatevector local) — nenhuma
   vantagem quântica fingida; documentado explicitamente abaixo.

---

## 🛠️ Tecnologias

| Categoria | Stack |
|---|---|
| Linguagem | Python 3.10.8 |
| Numérico | NumPy, SciPy (`linprog`, método HiGHS), pandas, matplotlib |
| Otimização clássica | Pyomo + `appsi_highs`, OR-Tools (instalado, não usado nesta rodada — ver Roadmap) |
| Computação quântica | Qiskit 1.4 + `qiskit-optimization` 0.7 + `qiskit-algorithms` 0.4 + `qiskit-aer` 0.17 |
| Testes | pytest |

---

## 📊 Resultados

Última execução real de `python -m benchmarks.compare_methods` (tabela completa gerada em
[`benchmarks/results.md`](benchmarks/results.md); instância: PETR4/VALE3/ITUB4, orçamento=2):

| Método | Tempo (s) | Selecionados | Risco quadrático | Shortfall esperado |
|---|---|---|---|---|
| Brute force (referência) | 0,0001 | VALE3, ITUB4 | 0,0205 | 0,1064 |
| LP (relaxação linear) | 0,0045 | PETR4, VALE3 | 0,0285 | 0,0561 |
| MILP (Pyomo + HiGHS) | 0,1893 | PETR4, VALE3 | 0,0285 | 0,0561 |
| Estocástico 2 estágios (forma extensiva) | 0,0342 | PETR4, VALE3 | 0,0285 | 0,0561 |
| Benders decomposition (2 iterações) | 0,0715 | PETR4, VALE3 | 0,0285 | 0,0561 |
| QUBO/QAOA (statevector) | 1,4095 | VALE3, ITUB4 | 0,0205 | 0,1064 |

**Achado real:** LP/MILP/estocástico/Benders convergem todos para a mesma carteira (PETR4+VALE3,
ótima pela métrica de shortfall), enquanto QAOA e a busca exaustiva convergem para VALE3+ITUB4 (ótima
pela métrica quadrática média-variância) — os dois grupos de métodos não estão "errados" um em relação
ao outro; estão otimizando riscos diferentes por construção. QAOA foi, como esperado, o método mais
lento (simulação estatevector local, sem nenhuma vantagem quântica real nesta escala de 3 qubits).

**Suíte de testes:** `pytest -v` → **14 passed** (30,19s), 1 warning (`PendingDeprecationWarning`
interno do Qiskit sobre `NLocal`, não relacionado ao código deste projeto).

**Bug real corrigido:** a API do rascunho v1 (`from qiskit.algorithms import QAOA`,
`qiskit.primitives.Estimator`) não funciona mais — `qiskit.algorithms.QAOA` foi removido em Qiskit
≥1.0 (migrou para `qiskit_algorithms`), e o primitive V1 `Estimator`/`Sampler` é incompatível com a
pipeline interna atual. Corrigido usando `qiskit_algorithms.QAOA` + `qiskit.primitives.StatevectorSampler`
(V2) — detalhe completo em [Desenvolvimento Experimental](#-desenvolvimento-experimental).

---

## 🖼️ Evidências

<p align="center">
<a href="Captura%20de%20tela%202025-08-20%20131417.jpg"><img src="Captura%20de%20tela%202025-08-20%20131417.jpg" width="520"></a>
</p>
<p align="center"><sub>Rascunho v1 (agosto/2025) — saída real do notebook original: QAOA e o solver
clássico de referência concordando na seleção de ativos. Nota honesta: esta captura usa uma instância
de <strong>4 ativos</strong> (PETR4, VALE3, ITUB4, ABEV3) do rascunho original, diferente da instância
de 3 ativos (PETR4, VALE3, ITUB4) usada no laboratório v2 descrito neste README — preservada como peça
histórica, não re-executada.</sub></p>

---

## 🚀 Aplicações

- Portfólio técnico demonstrando competência em otimização matemática clássica (LP/MILP/estocástica/
  decomposição) e computação quântica aplicada (QUBO/QAOA), lado a lado, com comparação honesta;
- Material de referência para discutir trade-offs reais entre paradigmas de otimização em entrevistas
  técnicas — cada método tem número medido, não só nome na lista de tecnologias;
- Esqueleto reaproveitável (instância + 5 solvers + benchmark) para aplicar o mesmo comparativo a
  outros problemas de alocação (scheduling, energy dispatch — ver Roadmap).

---

## 🔭 Visão de Longo Prazo

```text
v0.1  Rascunho — QUBO+QAOA isolado, 4 ativos fictícios (ago/2025, preservado intacto)
  ↓
v0.2  Laboratório comparativo — LP/MILP/estocástico/Benders/QAOA sobre a mesma instância,
      14 testes, benchmark real (2026-10-07)
  ↓
v0.3  (planejado) Escala maior (6–10 ativos) + segundo problema (scheduling/energy dispatch)
      resolvido pelos mesmos 5 métodos + Benders com master inteiro
  ↓
v0.4  (depois, fora de escopo) SDDP/PDDE para o problema multiestágio
  ↓
v0.5  (depois, fora de escopo) HPC/paralelização real (Dask/Ray) + profiling antes de otimizar
  ↓
v0.6  (depois, fora de escopo) Port de subproblemas críticos para C++/OpenMP
  ↓
v1.0  (depois, não comprometido) Mesmo QUBO rodado em hardware quântico real (IBM Quantum),
      overhead de fila e erro de hardware documentados honestamente
```

---

## 🗺️ Roadmap

Detalhamento completo: [`ROADMAP.md`](ROADMAP.md).

- **F0 — Rascunho** ✅ Concluída (ago/2025) — toy problem de seleção de portfólio via QUBO+QAOA (v1,
  preservado intacto).
- **F1 — MVP comparativo clássico vs. quântico** ✅ Concluída (2026-10-07) — instância compartilhada,
  LP, MILP, estocástico de 2 estágios com recurso real, Benders real, QUBO/QAOA corrigido, benchmark
  real, 14 testes.
- **F2 — Escala e robustez** ⏳ Planejada — expandir para 6–10 ativos; segundo problema do mesmo
  esqueleto (scheduling ou energy dispatch); Benders com master inteiro (branch-and-cut); explorar
  CVXPY/Julia-JuMP.
- **F3 — SDDP/PDDE** ⏳ Planejada (fora de escopo nesta rodada) — programação dinâmica estocástica
  dual para o problema multiestágio; comparação SDDP vs. Benders de 2 estágios vs. forma extensiva.
- **F4 — HPC / paralelização real** ⏳ Planejada (fora de escopo nesta rodada) — paralelizar
  subproblemas de Benders (multiprocessing/Dask/Ray), com profiling real antes de qualquer
  paralelização (não necessário na escala atual: 8 cenários resolvem em milissegundos).
- **F5 — Port para C++/OpenMP** ⏳ Planejada (fora de escopo nesta rodada) — portar só os
  subproblemas mais custosos em escala maior, mantendo a API Python como orquestração.
- **F6 — Hardware quântico real** ⏳ Planejada (fora de escopo, não comprometida) — mesmo QUBO em
  backend real via IBM Quantum ou simulador com ruído, com overhead e (não-)vantagem documentados
  honestamente.

---

## 🕓 Histórico e Mudanças

| Versão | Data | O que mudou |
|---|---|---|
| [0.1.0](CHANGELOG.md) | 2025-08-20 | Rascunho inicial: seleção de portfólio (PETR4/VALE3/ITUB4/ABEV3) via QUBO+QAOA (`qiskit-optimization`/`qiskit-aer`). |
| [0.2.0](CHANGELOG.md) | 2026-10-07 | Laboratório comparativo: instância compartilhada, LP, MILP, estocástico, Benders, QUBO/QAOA corrigido, benchmark real, 14 testes, API do Qiskit atualizada. |

Histórico completo: [CHANGELOG.md](CHANGELOG.md).

---

## 🔮 Próximos Passos

**Concluído nesta versão (0.2.0):**
- Os 5 métodos sobre a mesma instância, com benchmark real e 14 testes — ver "Resultados".

**Próximos técnicos (o que eu faria numa v3, ver Roadmap F2 em diante):**
- Expandir a instância para 6–10 ativos e medir como cada método escala;
- Segundo problema do mesmo esqueleto (scheduling ou energy dispatch) resolvido pelos mesmos 5
  métodos, para generalizar a comparação além de portfólio;
- Benders com master inteiro (branch-and-cut), não só relaxação contínua;
- SDDP/PDDE, HPC real (Dask/Ray), port C++/OpenMP, hardware quântico real — todos deliberadamente
  fora de escopo nesta rodada, sem data comprometida.

Nenhum item desta lista depende de credencial ou ação externa do usuário — são todos trabalho técnico
puro, sequenciado por prioridade no `ROADMAP.md`.

---

## ▶️ Como rodar localmente

Pré-requisitos: Python 3.10 (testado com 3.10.8); ambiente limpo recomendado (ver nota sobre conflito
de versões do Qiskit em `requirements.txt`).

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt

pytest -v                              # 14 passed
python -m benchmarks.compare_methods   # gera benchmarks/results.md e results.json
```

O rascunho v1 (`main.py`, `portfolio_qaoa.py`, `qaoa_portfolio*.ipynb`) usa `requirements.txt.txt`
(pins antigos, não compatíveis com o ambiente do v2) — mantido apenas como peça histórica, não
executado nesta revisão.

---

## 📁 Estrutura do repositório

```text
optimization/        5 métodos de otimização sobre a instância compartilhada (LP/MILP/estocástico/
                      Benders/QAOA) — ver "Arquitetura"
benchmarks/           compare_methods.py + results.md/.json (saída real, gerada)
tests/                14 testes (instância + 5 métodos)
main.py, portfolio_qaoa.py, *.ipynb   v1 — rascunho original, preservado intacto, não sobrescrito
requirements.txt      pins novos e corretos (Qiskit >=1.0,<2.0 + Pyomo/HiGHS)
requirements.txt.txt  pins antigos do v1 (Qiskit <1.0) — não usar com o código novo
CHANGELOG.md          histórico de versões (Keep a Changelog / SemVer)
ROADMAP.md             fases F0–F6, com itens explicitamente marcados "depois"
WORKLOG.md             log da sessão de implementação (diagnóstico, correções, validação)
```

Não versionado: `__pycache__/`, `.pytest_cache/`, `.deepeval/` (cache local de ferramentas de
desenvolvimento).

---

## 📚 Documentação

| Documento | Conteúdo |
|---|---|
| [CHANGELOG.md](CHANGELOG.md) | Histórico de versões (Keep a Changelog / SemVer) |
| [ROADMAP.md](ROADMAP.md) | Fases F0–F6, com itens explicitamente fora de escopo marcados "depois" |
| [WORKLOG.md](WORKLOG.md) | Log da sessão: diagnóstico do ambiente, bug de API do Qiskit, implementação, validação |
| [benchmarks/results.md](benchmarks/results.md) | Saída real e completa da última execução do benchmark |

---

## ⚠️ Limitações

- **Escala de brinquedo**: 3 ativos fictícios, 8 cenários — nenhuma conclusão de escalabilidade real
  pode ser tirada desta versão; é o item #1 do Roadmap (F2);
- **QAOA sem vantagem quântica**: simulação estatevector local, sem ruído, sem hardware real — foi o
  método mais lento do benchmark (~1,41s), documentado honestamente, não escondido;
- **Dois modelos de risco coexistindo** (quadrático para QAOA, shortfall linear para os métodos
  clássicos) significam que os 5 métodos não estão tecnicamente otimizando o mesmo objetivo — o
  benchmark reavalia todas as soluções nas duas métricas para mitigar isso, mas a comparação direta de
  "quem venceu" exige ler a tabela completa, não só uma coluna;
- **Benders de 2 estágios apenas** — SDDP/PDDE (multiestágio) está fora de escopo nesta rodada;
- **Sem arquivo `LICENSE`** neste repositório — ver "Licença" abaixo;
- **v1 (rascunho original) não foi atualizado nem re-executado** — preservado intacto como peça
  histórica; usa pins de dependência antigos e incompatíveis com o ambiente do v2.

---

## Status

🟡 **MVP técnico funcional** — LP, MILP, estocástico de 2 estágios, Benders e QUBO/QAOA rodando na
mesma instância, 14 testes passando, benchmark real medido. Ainda de escala de brinquedo (3 ativos
fictícios); SDDP/PDDE, HPC real, C++/OpenMP e hardware quântico real ficaram fora desta rodada.

---

## Contexto / Observações

Peça de portfólio pessoal — não afiliado a nenhuma instituição financeira real; os ativos (PETR4,
VALE3, ITUB4) são usados apenas como rótulos ilustrativos, os retornos/covariâncias/cenários são
sintéticos (seed fixa), não dados de mercado reais. Nenhuma recomendação de investimento é implícita.
Todos os números em "Resultados" vêm de execução real medida nesta máquina (`time.perf_counter`,
`pytest`), nunca de estimativa ou simulação de ferramenta de terceiros. Projeto independente dentro do
mesmo portfólio pessoal do autor (ver `ArgusAI`, auditado na mesma sessão); sem integração técnica
direta entre os dois repositórios.

---

## 🔗 Projetos Relacionados

Projeto independente dentro do mesmo portfólio pessoal — sem integração técnica direta com os demais
repositórios. Ligação de contexto: foi o item de prioridade #2 da mesma auditoria de portfólio que
produziu as últimas três versões do `ArgusAI` (RAG avançado, governança de MDM, engenharia de dados).

---

## 🤖 Autor

**Yuri Fernando Dubbern**

Engenharia Elétrica · Ciência da Computação · Inteligência Artificial ·
Sistemas Embarcados · Projeto de Hardware · Pesquisa e Desenvolvimento

[LinkedIn](https://www.linkedin.com/in/yuridubbern) · [GitHub](https://github.com/Yuri-Fernando) · [Lattes](http://lattes.cnpq.br/7151392692642166) · [Linktree](https://linktr.ee/yuri.f.dubbern)

---

## Licença

Nenhuma licença formal definida neste repositório (sem arquivo `LICENSE`). Peça de portfólio pessoal;
uso, redistribuição ou reuso comercial não autorizados sem contato prévio com o autor. Dados
financeiros usados são sintéticos/ilustrativos — ver "Contexto / Observações".
