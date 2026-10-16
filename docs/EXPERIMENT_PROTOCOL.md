# Protocolo experimental

Todos os experimentos rodam offline em CPU por `python -m experiments.run --config <yaml>`. Cada
execução cria um diretório novo `results/<experimento>/<run_id>/` (nunca sobrescreve) com:

| Arquivo | Conteúdo |
|---|---|
| `manifest.json` | run_id, timestamp UTC, git SHA + working tree suja, Python, plataforma, versões das bibliotecas, dispositivos detectados, config resolvida + `config_hash`, linha de comando, status, tempo de parede |
| `records.jsonl` | um registro por unidade experimental (método × instância × seed × config) |
| `raw_counts.jsonl.gz` | contagens brutas de cada execução quântica, referenciadas por `record_id` |
| `summary.md`, `figures/` | gerados por `experiments.analyze` **somente** a partir de `records.jsonl` |

## Regras

1. **Mesmo objetivo para comparar algoritmos.** Trilha `algorithm_benchmark`: todos os métodos de uma
   instância compartilham `objective_id` (testado). Trilha `model_comparison`
   (`benchmarks/compare_methods.py`) compara formulações de risco e não entra em rankings.
2. **Solução só se viável.** A solução do QAOA é a melhor amostra com `Σx = k`; sem amostra viável,
   `status = no_feasible_sample`.
3. **Ideal ≠ amostrado ≠ ruidoso.** Métricas `*_exact` vêm das probabilidades exatas da evolução
   ideal; métricas amostradas vêm de `shots` finitos; métricas ruidosas vêm do Aer com modelo de ruído.
4. **Pseudo-réplicas não contam como independentes.** Com inicialização determinística e objetivo exato,
   seeds diferentes produzem a mesma otimização; a análise remove duplicatas (`indep.`) antes de
   calcular média e IC das métricas exatas.
5. **ICs.** Bootstrap percentil 95% sobre execuções independentes; proporções de shots com Wilson.
6. **Gap relativo** só com `|f*| > 1e-12`.
7. **Baseline aleatório obrigatório.** `P(ótimo)` do QAOA é comparado com `n_ótimos / C(n,k)` e com a
   amostragem aleatória viável usando o MESMO número de amostras.
8. **Hardware.** Nada é rotulado GPU/QPU sem execução real nesses dispositivos (`is_real_hardware`,
   `device`). QPU só com `--allow-qpu`; CI recusa.

## Experimentos

| ID | Config | Pergunta | Desenho |
|---|---|---|---|
| E0 | `e0_equivalence.yaml` | As formulações coincidem? | 2 domínios × n∈{3,4,5,6,8} × 5 seeds; todas as bitstrings |
| E1 | `e1_ideal_qaoa.yaml` | Qualidade do QAOA ideal × clássicos | n∈{4..12}, p∈{1..4}, 2 mixers, 2 inicializações, 10 seeds × 3 instâncias |
| E1b | `e1b_optimizers_shots.yaml` | Otimizador, inicialização, shots, objetivo exato × amostrado | n=8, p=2, 10 seeds × 2 instâncias |
| E1c | `e1c_penalty.yaml` | Sensibilidade a ρ | fator ∈ {0,02…2} × ρ_seguro, n∈{6,8} |
| E2 | `e2_hardware_aware.yaml` | Custo de conectividade | 4 backends fake × níveis {1,3} × 3 seeds de transpilation |
| E3 | `e3_noise.yaml` | Degradação por ruído | transferência: parâmetros do ideal executados em 8 regimes, 4096 shots, 10 seeds |
| E4 | `e4_scalability.yaml` | Tempo/memória vs n | n até 20, p=1 |
| E5 | `e5_gpu.yaml` | CPU × GPU | só executa GPU se o Aer a expuser |
| E6 | `e6_qpu.yaml` | QPU real | dry-run por padrão; sem opt-in registra `not_executed` |
| E7 | `e7_scheduling.yaml` | Segundo domínio | como E1 com n∈{6..12}, p∈{1..3} |

### Protocolo de transferência (E3)

Os parâmetros são otimizados na simulação ideal exata e o **mesmo circuito** é executado sob cada
regime com a mesma seed e o mesmo número de shots. Isso isola o efeito do ruído sobre a execução;
não mede a capacidade do otimizador de compensar ruído (otimização sob ruído é trabalho futuro).
Com uma instância por tamanho, as seeds replicam a amostragem/trajetórias de ruído, não a otimização.

### Orçamento computacional

Os produtos cartesianos foram dimensionados para caber em minutos numa CPU de desktop (tempo de
parede de cada execução fica no manifesto). E4 para em n=20 porque a simulação estatevetorial dobra de
custo a cada qubit; isso é limite da simulação clássica, não do algoritmo.

## Ameaças à validade

- Instâncias sintéticas e pequenas (n ≤ 12 na qualidade; ≤ 20 em tempo); nenhuma extrapolação.
- `maxiter` fixo e poucos otimizadores; outra configuração pode mudar o ranking entre mixers.
- Backends fake têm taxas de erro sintéticas (`GenericBackendV2`) ou um snapshot antigo
  (`Fake27QPulseV1`); não representam a calibração atual de nenhum dispositivo.
- Tempos de parede medidos num único host Windows, com processos concorrentes; usar como ordem de
  grandeza.
