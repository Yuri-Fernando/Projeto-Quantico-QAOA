# Relatório técnico — QAOA × métodos clássicos no MESMO objetivo, com topologia e ruído simulados

Relatório interno estilo artigo, gerado a partir das execuções em `results/` (commits `fc936b3` e
`2b5c85f`, working tree limpa em todos os manifests). Não é publicação, não passou por revisão por
pares e não envolve hardware quântico real.

## Resumo

Avaliamos QAOA simulado contra baselines clássicos em problemas de seleção com cardinalidade
(`min xᵀQx` s.a. `Σx = k`), em dois domínios sintéticos — portfólio média-variância e seleção de tarefas
por turno com conflito de recursos — sempre sobre a mesma função-objetivo. Comparamos duas políticas de
viabilidade (mixer X + penalidade; mixer XY em anel + estado de Dicke), medimos o custo de compilação em
backends fake e o efeito de ruído sob um protocolo de transferência. Nas instâncias medidas (n ≤ 12
para qualidade), MILP linearizado e enumeração certificam o ótimo em ≤ 0,2 s e simulated annealing o
encontra em 100% das execuções. O QAOA com mixer X + penalidade não concentra probabilidade no ótimo
acima do sorteio uniforme de soluções viáveis para n ≥ 10 (em n=8, no máximo 1,15×). O XY + Dicke concentra (até ~10–13× o sorteio
uniforme no ideal), mas custa ~3,6× mais portas de dois qubits após roteamento, e sob ruído de magnitude
realista sua probabilidade de ótimo por shot cai abaixo do sorteio uniforme em n=8.

## 1. Problema e hipóteses

- H1: o QAOA ideal concentra probabilidade no ótimo acima do sorteio uniforme viável.
- H2: preservar a cardinalidade no ansatz (XY + Dicke) melhora a qualidade em relação à penalidade.
- H3: a vantagem de H2 sobrevive à compilação para topologias restritas e a ruído realista.
- H4: o QAOA é competitivo com baselines clássicos de mesmo objetivo em qualidade e custo.

## 2. Materiais

- Python 3.10.8, Qiskit 1.4.6, qiskit-aer 0.17.2, Pyomo 6.10.1 + HiGHS 1.15.1 (lock em
  `requirements-lock.txt`). Windows 11, CPU; GPU NVIDIA presente mas não usada pelo Aer (ver §5.6).
- Instâncias sintéticas reprodutíveis: portfólio (`Σ = BBᵀ + diag(d)`, PSD por construção) e
  escalonamento (`w_j ~ U(0,5; 1,5)`, recursos com prob. 0,25, `α = 0,6`); `k = ⌊n/2⌋`.

## 3. Métodos

Formulação em `docs/MATHEMATICAL_FORMULATION.md`; protocolo em `docs/EXPERIMENT_PROTOCOL.md`.
Baselines: enumeração (oráculo), MILP McCormick (HiGHS), relaxação LP, simulated annealing (2000 passos
de troca), amostragem aleatória viável (1024 amostras). QAOA: circuito explícito, laço COBYLA (ou SPSA)
sobre simulação ideal exata, 1024 shots finais; solução = melhor amostra viável.

## 4. Validação (E0)

50/50 instâncias (2 domínios, n ∈ {3,4,5,6,8}, 5 seeds) com paridade completa: `|f − f_original|`,
`|E_QUBO − (f + ρd²)|`, `|E_Ising − E_QUBO|` e `|diag(SparsePauliOp) − E_QUBO|` ≤ 4,4e-16; MILP ==
enumeração; LP ≤ MILP; estado fundamental do QUBO com ρ seguro = ótimo viável. Run:
`results/e0_equivalence/20261015T192218Z-251c73`.

## 5. Resultados

### 5.1 Qualidade no ideal (E1, portfólio, 10 seeds × 3 instâncias)

`P(ótimo)` exato dividido pelo sorteio uniforme viável (`÷unif`), inicialização aleatória (30 otimizações
independentes por célula):

| n | X p=1 | X p=4 | XY p=1 | XY p=4 |
|---|---|---|---|---|
| 4 | 0,59 | 1,69 | 1,68 | 4,85 |
| 6 | 0,64 | 1,18 | 0,90 | 3,56 |
| 8 | 0,48 | 0,95 | 0,93 | 1,55 |
| 10 | 0,38 | 0,80 | 1,35 | 1,55 |
| 12 | 0,39 | 0,82 | 1,04 | 2,67 |

Com inicialização *linear ramp* (determinística; 3 otimizações independentes por célula, ICs largos) o
XY chega a 6,6–13× em alguns pontos (ex.: n=12, p=4: 13,0×, IC95 de P(ótimo) [0,0006; 0,040]).
P(viável) exato do mixer X fica em 0,2–0,95 — parte dos shots é desperdiçada em estados inviáveis.

**Melhor amostra = ótimo** (1024 shots), comparada com 1024 sorteios aleatórios viáveis: em n=12, a
amostragem aleatória acerta em 73% das execuções; QAOA X 13–60%; QAOA XY 33–70% (conforme p e
inicialização). SA e MILP: 100%.
Run: `results/e1_ideal_qaoa/20261015T194733Z-6d86da`.

→ H1 confirmada só para XY (e para X apenas em n ≤ 6 com p alto). H2 confirmada no ideal. H4 refutada
nestas instâncias.

### 5.2 Otimizador, inicialização, shots (E1b, n=8, p=2)

- COBYLA ≥ SPSA em P(ótimo) exato (XY: 0,072 vs 0,055; X: 0,011 vs 0,011) com menos avaliações.
- Objetivo estimado por shots ≈ objetivo exato em qualidade (XY COBYLA: 0,063 vs 0,072), mas o custo
  em shots totais sobe de ~1,8 mil para 86–91 mil (COBYLA) e 543 mil (SPSA) por execução.
- Inicialização: *linear ramp* 0,089 > *uniform_small* (política da v0.2.0) 0,071 > aleatória 0,020 (XY).
- Shots finais 256 → 4096: fração de execuções cuja melhor amostra é ótima sobe de 0,89 para 1,00
  (X) e de 0,97 para 0,99 (XY). O sorteio aleatório com 1024 amostras acerta 100% nesse tamanho
  (n=8 tem só 70 seleções viáveis); não foi medido com 256.

### 5.3 Penalidade (E1c, mixer X, p=2)

A penalidade crítica medida é 3,6% (portfólio) a 9,8% (escalonamento) da penalidade segura em média
(máx. 41%; E0). Em n=6, reduzir ρ de 1× para 0,02× o valor seguro aumenta `÷unif` de 0,98 para 2,15
ao custo de P(viável) cair de 0,77 para 0,38; em n=8 o ganho é menor (0,82 → 1,30). Nenhuma execução
ficou sem amostra viável. Penalidade "provadamente segura" ≠ penalidade boa para o otimizador.

### 5.4 Topologia e compilação (E2, 960 transpilações, todas aceitas pelo `Target`)

n=12, p=1, nível 3 (média de 3 seeds de transpilation):

| Mixer | 2Q lógicas | 2Q físicas all-to-all | 2Q físicas linha | 2Q físicas heavy-hex 19q | SWAPs heavy-hex | depth lógica → física (heavy-hex) |
|---|---|---|---|---|---|---|
| X (portfólio) | 66 | 132 | 261 | 259 | 56 | 25 → 214 |
| XY+Dicke (portfólio) | 203 | 537 | 947 | 952 | 195 | 120 → 1392 |
| XY+Dicke (escalonamento) | 168 | 468 | 962 | 858 | 176 | 117 → 1376 |

- A penalidade torna o grafo de custo completo: com mixer X, portfólio e escalonamento compilam
  **identicamente**. A esparsidade do escalonamento só reduz portas com o XY (sem penalidade).
- O roteamento ~dobra as portas 2Q; SWAPs crescem de 2–3 (n=4) para 56–60 (n=12) no mixer X.
- `Fake27QPulseV1` e heavy-hex sintético dão contagens semelhantes; a linha não é muito pior aqui.

### 5.5 Ruído (E3, transferência, 10 seeds, 4096 shots)

P(ótimo) por shot, XY+Dicke p=2 (uniforme viável: n=4 0,167; n=6 0,050; n=8 0,014):

| n | ideal | leitura 3% | despolarizante p2=0,5% | p2=2% | fake heavy-hex | fake27 snapshot |
|---|---|---|---|---|---|---|
| 4 | 0,516 | 0,457 | 0,364 | 0,153 | 0,261 | 0,275 |
| 6 | 0,276 | 0,228 | 0,125 | 0,026 | 0,049 | 0,044 |
| 8 | 0,169 | 0,133 | 0,039 | 0,004 | 0,010 | 0,006 |

Taxa viável do XY cai de 1,00 (ideal) para 0,21–0,29 nos backends fake em n=8. O mixer X, cuja
P(ótimo) ideal já era próxima do aleatório, muda pouco. → H3 refutada: a vantagem ideal do XY não
sobrevive ao ruído porque ele usa ~3,6× mais portas 2Q. Run: `results/e3_noise/20261015T214030Z-2cac2f`.

### 5.6 CPU × GPU (E5) e QPU (E6)

- GPU: **não executado** — `available_devices() == ('CPU',)` apesar da RTX 3060 Ti no host. CPU Aer
  statevector, 1024 shots, circuito p=1: n=10 0,013 s; n=14 0,022 s; n=18 0,116 s; n=22 0,93 s (mediana
  de 3). Run: `results/e5_gpu/20261015T192247Z-47dd1d`.
- QPU: **não executado** — sem `--allow-qpu`; caminho real `BLOCKED_BY_CONFIGURATION`
  (`results/e6_qpu/20261015T192330Z-6b4304`).

### 5.7 Escalabilidade (E4)

Portfólio, 3 instâncias por n, QAOA p=1 com inicialização *linear ramp* (3 otimizações independentes
por célula; 9 execuções contando as seeds de amostragem). Medianas de tempo de parede (CPU):

| n | enumeração (s) | MILP McCormick (s) | SA (s) | QAOA X total (s) | QAOA XY total (s) | statevector teórico | pico tracemalloc XY |
|---|---|---|---|---|---|---|---|
| 8 | 0,0002 | 0,048 | 0,092 | 0,034 | 0,018 | 4 KiB | 0,3 MB |
| 12 | 0,0010 | 0,204 | 0,087 | 0,132 | 0,096 | 64 KiB | 1,3 MB |
| 16 | 0,022 | 0,751 | 0,098 | 0,804 | 1,198 | 1 MiB | 27 MB |
| 20 | 0,344 | 4,19 | 0,098 | 22,1 | 25,7 | 16 MiB | 528 MB |

- Todos os MILP terminaram `optimal`; o tempo do MILP cresce mais rápido que o do SA, que fica ~0,1 s.
- O custo de SIMULAR o QAOA cresce ~3,5–7× a cada 2 qubits entre n=14 e 20; o pico de memória Python é ~30× o
  statevector teórico (matrizes de base e energias de `2^n × n`). Pico de RSS do processo: 725 MB.
  Isso mede o simulador, não um QPU.
- Melhor amostra = ótimo (1024 shots): sorteio aleatório viável 100% até n=12 e **0%** de n=14 em diante
  (C(14,7)=3432 > 1024); QAOA XY 67–78% em n=10–16, 11% em n=18 e 0% em n=20; QAOA X 0% a partir de
  n=14; SA 100% em todos os tamanhos.

É o único regime medido em que o QAOA (XY, ideal) supera o baseline aleatório com o mesmo orçamento de
amostras — ainda abaixo do SA e com amostra pequena de otimizações. Run:
`results/e4_scalability/20261015T214902Z-fe781a`.

### 5.8 Segundo domínio (E7, escalonamento, 10 seeds × 3 instâncias)

| n | ÷unif X | ÷unif XY | P(viável) X | melhor amostra ótima X | XY | aleatório | SA |
|---|---|---|---|---|---|---|---|
| 6 | 0,68 | 3,43 | 0,71 | 1,00 | 1,00 | 1,00 | 1,00 |
| 8 | 0,67 | 2,34 | 0,60 | 1,00 | 0,97 | 1,00 | 1,00 |
| 10 | 0,54 | 2,17 | 0,55 | 0,84 | 0,91 | 0,93 | 1,00 |
| 12 | 0,51 | 3,03 | 0,45 | 0,28 | 0,79 | 0,70 | 1,00 |

Mesma tendência do portfólio para o mixer X. Diferença: em n=12 o XY acertou o ótimo com a melhor
amostra em 79% das execuções, acima do sorteio aleatório (70%) — mas abaixo do SA (100%) e no regime
ideal, sem ruído. Run: `results/e7_scheduling/20261015T192954Z-828756`.

## 6. Ameaças à validade

- Escala pequena e sintética; nenhum resultado deve ser extrapolado para n maior nem para dados reais.
- Um único `maxiter`, dois otimizadores, sem *warm start*, sem CVaR, sem mitigação de erro.
- Ruído por transferência: não mede otimização sob ruído.
- Backends fake com erros sintéticos ou snapshot antigo; não representam um dispositivo atual.
- A comparação de "melhor amostra ótima" depende do orçamento de shots escolhido (1024).

## 7. Conclusão

Nas instâncias medidas, o baseline clássico de mesmo objetivo é superior em qualidade, custo e
garantia. O QAOA com preservação de cardinalidade é a melhor variante quântica no ideal, mas o custo
de compilação o torna a mais frágil sob ruído — um trade-off que só aparece quando topologia e ruído
entram no experimento. Decisão técnica derivada: `docs/adr/ADR-001-quando-nao-usar-qaoa.md`.
Próximos experimentos: otimização sob ruído, mitigação de erro com overhead medido, mixers com menor
custo de compilação (ex.: XY em pares paralelos), GPU em host Linux e microexperimento em QPU autorizado.
