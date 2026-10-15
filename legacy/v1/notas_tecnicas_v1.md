# Notas técnicas do rascunho v1 (agosto/2025)

Trechos técnicos das notas de planejamento originais do rascunho, preservados como registro histórico
(o arquivo original de notas pessoais não é versionado). Texto mantido como escrito na época, só
reorganizado em seções.

## Ideia inicial

Simulação de portfólio financeiro via QAOA, inspirada em trabalhos de *quantum finance* que aplicam
algoritmos quânticos à otimização de carteiras com exemplos da B3 e código em Jupyter Notebook.
Alternativa considerada na época: um benchmark com o algoritmo de Grover em busca/inversão de função.

## O que o rascunho deveria entregar

- Solução QAOA (seleção de ativos + valor do objetivo);
- Comparação clássica por busca exaustiva;
- Instância toy (PETR4, VALE3, ITUB4, ABEV3), limpa e reproduzível;
- Fluxo: problema financeiro pequeno → QUBO → QAOA.

## O que foi feito no rascunho

- Um `QuadraticProgram` representando a função objetivo da carteira (minimizar risco ou combinar
  retorno × risco);
- Restrições simples (como número máximo de ativos na carteira);
- QAOA como otimizador combinatório; resultado do tipo `[1,0,1,0,0]` (1 → o ativo entra, 0 → não entra).

Observação da época: o algoritmo não olha para preços, retornos históricos ou correlações por conta
própria — ele resolve o problema matemático fornecido; a qualidade da carteira depende dos dados
colocados no modelo.

## Próximos passos planejados na época

1. Escolher 5–10 ações da B3; estimar retorno esperado (média histórica) e risco (variância);
2. Calcular a matriz de covariância;
3. Construir a função objetivo (ex.: minimizar risco para um retorno mínimo);
4. Rodar o QAOA com esses dados, mantendo o comparativo clássico;
5. Atribuir pesos proporcionais a retorno/risco para uma alocação mais realista;
6. Puxar dados reais via `yfinance`;
7. Gráficos: barras dos ativos escolhidos, retorno esperado × risco, heatmap da covariância.

## O que aconteceu depois

O projeto seguiu outro caminho: v0.2.0 comparou formulações clássicas (LP, MILP, estocástico, Benders)
com QAOA, e a v0.3.0 construiu o benchmark de mesmo objetivo com estudo de compilação e ruído — ver o
[README principal](../../README.md). Dados reais de mercado (`yfinance`) não foram incorporados; todas as
instâncias atuais são sintéticas.
