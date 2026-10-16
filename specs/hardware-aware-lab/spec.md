# Spec — Laboratório hardware-aware de otimização clássica × QAOA (v0.3.0)

Origem: auditoria técnica de 2026-10-15 sobre o commit `c894c73` (v0.2.0). Cada requisito abaixo
rastreia a um item da auditoria (P0.x, P1.x, P2.x, Epics A–E, testes T01–T18) ou a um fato verificado
no código.

## Problema

A v0.2.0 compara LP/MILP/estocástico/Benders (risco de *shortfall*) com QAOA (risco média-variância)
— objetivos diferentes. O benchmark mede formulações de risco, não algoritmos. O QAOA não expõe
distribuição de amostras, viabilidade, QUBO efetivo, circuito físico, ruído nem custo de recursos, e
roda numa única instância de 3 variáveis.

## Objetivos

1. Comparar algoritmos sobre a **mesma** função-objetivo e as mesmas restrições (P0.1).
2. Tornar o QAOA auditável: QUBO/Ising exportados, distribuição de shots, viabilidade (P0.2–P0.5).
3. Medir o efeito de topologia, transpilation e ruído com backends fake locais (P1.1, P1.2).
4. Gerar instâncias escaláveis e reproduzíveis, com múltiplas seeds e ICs (P1.3, P0.3).
5. Orquestrar CPU/GPU/QPU com detecção real de recursos e guardas de custo (P2.1, P2.2).
6. Segundo domínio de aplicação industrial com comparação justa (E7).
7. Reprodutibilidade de engenharia: CI, pyproject, lock, manifest por execução (P1.4).

## Não-objetivos

- Alegar vantagem quântica; executar jobs pagos; instalar dependências de GPU/QPU sem autorização.
- SDDP/PDDE, port C++/OpenMP, Dask/Ray/Kubernetes, aplicação web (auditoria §11, "não priorizar").
- Escolher licença (decisão do proprietário, auditoria §9).
- Reescrever os módulos v0.2.0 ou apagar arquivos/histórico.

## Requisitos funcionais

- **FR-1** Problema canônico `min f(x) = x^T Q x + c, s.a. Σx = k` com `objective_id` e hash de instância.
- **FR-2** QUBO penalizado `E(x) = f(x) + ρ(Σx − k)^2` com convenção triangular superior, offset e ρ
  exportados; política de penalidade fixa e "segura" (limite que garante ótimo viável).
- **FR-3** Mapeamento QUBO → Ising (`h`, `J`, offset) e `SparsePauliOp`, com ordem de bits documentada.
- **FR-4** Baselines clássicos do MESMO objetivo: enumeração (oráculo), MILP linearizado (McCormick,
  Pyomo/HiGHS), relaxação LP do MILP linearizado, simulated annealing e amostragem aleatória viável.
- **FR-5** QAOA instrumentado: profundidade `p`, otimizador (COBYLA, SPSA), inicialização, seed, shots,
  mixer X + penalidade e mixer XY em anel + estado de Dicke (preserva cardinalidade).
- **FR-6** Análise de amostras: contagens, `feasible_rate`, `invalid_shot_rate`, `P(ótimo)`, melhor
  bitstring viável, energia esperada, gap absoluto, gap relativo só com denominador não degenerado.
- **FR-7** Transpilation: métricas lógicas vs físicas (depth, portas, 2Q, SWAPs, layout, tempo) em
  backends fake (linha, heavy-hex sintético, snapshot `Fake27QPulseV1`, all-to-all).
- **FR-8** Regimes de ruído: ideal exato, só amostragem, readout, depolarizante de portas, derivado de
  backend; mesmo circuito/seed/shots; hash do modelo de ruído.
- **FR-9** Gerador de instâncias `n` arbitrário (Σ PSD), validação de parâmetros, estimativa de memória.
- **FR-10** Execução GPU somente se `AerSimulator.available_devices()` contiver `GPU`; caso contrário,
  registro explícito "não executado" e fallback CPU marcado.
- **FR-11** Adaptador IBM QPU com `--allow-qpu` obrigatório, credenciais via variável de ambiente,
  limite de shots/jobs, dry-run, bloqueio em CI; nunca chamado nos testes.
- **FR-12** CLI de experimentos por config YAML, manifest por execução (git SHA, versões, seeds, hashes),
  `runs.jsonl` e análise que regenera tabelas só a partir dos dados salvos.
- **FR-13** Segundo caso: seleção de tarefas por turno com conflito de recursos (mesma forma canônica).
- **FR-14** Benchmark de modelos (v0.2.0) separado do benchmark de algoritmos, com rótulos corrigidos.

## Restrições

- **CON-1** Os 14 testes da v0.2.0 continuam passando sem alteração de asserções.
- **CON-2** Tudo executável offline, sem token IBM nem GPU.
- **CON-3** Python 3.10 canônico; nada instalado em `G:\` (regra do ambiente).
- **CON-4** Nenhum resultado de GPU/QPU atribuído a simulação CPU; nada marcado concluído sem execução.
- **CON-5** Legado v1 preservado via `git mv` (histórico intacto).

## Critérios de aceite

- **AC-1** (P0.1/T01/T02) Para n ≤ 5 e todas as bitstrings: `f`, QUBO e energia Ising coincidem
  (tol. 1e-9); MILP linearizado == enumeração para várias instâncias.
- **AC-2** (P0.4/T03) Nenhuma solução reportada como válida com `Σx ≠ k`.
- **AC-3** (P0.5) Bug de dupla contagem do legado confirmado ou refutado por teste.
- **AC-4** (P1.1/T07/T08) Circuito transpilado aceito pelo `Target`; métricas preenchidas.
- **AC-5** (P1.2) Ideal × ruidoso comparados com mesmo problema/seed; reprodutível por seed.
- **AC-6** (Marco mínimo) ≥ 3 tamanhos, ≥ 10 seeds, shots instrumentados, ICs exportados.
- **AC-7** (T10/T11/T14) CLI offline funciona; sem `--allow-qpu` nenhuma chamada externa.
- **AC-8** (T12) GPU: paridade se disponível; skip explícito caso contrário.
- **AC-9** README/benchmark sem a alegação "QAOA == MILP"; resultados vêm de execuções salvas.
