# ADR-001 — Quando NÃO usar QAOA (e o que usar no lugar)

- Status: aceito (2026-10-15), baseado nos experimentos E1–E7 deste repositório
- Escopo: problemas de seleção com cardinalidade e objetivo quadrático (`CardinalityProblem`)

## Contexto

O laboratório compara QAOA simulado e métodos clássicos sobre a MESMA função-objetivo. A pergunta de
decisão para um cliente não é "o QAOA funciona?", e sim "ele é a melhor opção em qualidade, custo e
latência para este problema, hoje?".

## Evidência (resumida; detalhes em `docs/SCIENTIFIC_RESULTS.md`)

- MILP linearizado (HiGHS) e enumeração certificam o ótimo em ≤ 0,2 s até n=12; simulated annealing
  acha o ótimo em 100% das execuções medidas no E1 e no E7.
- QAOA com mixer X + penalidade não supera, em `P(ótimo)`, o sorteio uniforme de soluções viáveis
  para n ≥ 10 nas instâncias medidas (n=8: no máximo 1,15×); desperdiça shots em estados inviáveis.
- QAOA com mixer XY + Dicke concentra probabilidade acima do sorteio uniforme no regime ideal. Com 1024
  shots, em n=12, a melhor amostra foi ótima em 33–70% das execuções no portfólio (sorteio aleatório:
  73%) e em 79% no escalonamento (sorteio: 70%); SA: 100% em ambos. Em n=14–16 (E4, p=1, ideal) o XY
  acertou em 67–78% enquanto 1024 sorteios aleatórios não acertaram nenhuma vez — mas o SA acertou
  100% em ~0,1 s.
- Após compilação, o XY usa ~3,6× mais portas de dois qubits que o mixer X (E2), e sob ruído de
  magnitude realista sua P(ótimo) por shot em n=8 cai abaixo do sorteio uniforme (E3). Medido em
  simulação com backends fake.

## Decisão

Não usar QAOA como solver de produção para esta família de problemas na escala atual. Usar:

1. MILP/MIQP clássico (exato, com gap certificado) como primeira escolha;
2. heurísticas clássicas (SA, busca local) quando o tempo de resposta for mais restrito que o MILP;
3. QAOA apenas como objeto de P&D: estudo de mixers, compilação e ruído, com o baseline clássico
   sempre ao lado e o mesmo objetivo.

## Quando reavaliar

- Instâncias que o MILP não resolve dentro do orçamento de tempo (gap aberto) E com estrutura que
  favoreça o ansatz (ex.: restrições codificáveis no mixer, conectividade compatível com o hardware);
- Execução em QPU real com taxas de erro e latência de fila medidas, comparando custo por solução
  ótima encontrada contra o clássico;
- Evidência publicada de vantagem para a família de problemas em questão.

## Consequências

- O laboratório continua útil como banco de prova e material de capacitação.
- Qualquer proposta de uso de QPU a cliente precisa incluir o baseline clássico equivalente, o custo
  total (fila + execução + pós-processamento) e a probabilidade de obter o ótimo por job.
