# Projeto-Qu-ntico-Otimiza-o-de-Portf-lio-via-QAOA

Otimização de Portfólio com QAOA (Qiskit)

💡 Resumo do projeto:
Este projeto demonstra como aplicar algoritmos quânticos para seleção de portfólio financeiro, combinando retorno esperado e risco, utilizando o QAOA do Qiskit. A ideia central é modelar a escolha de ativos como um problema de otimização quadrática binária (QUBO), onde cada ativo pode ser selecionado (1) ou não (0) dentro de um orçamento definido.

🔹 Funcionalidades implementadas
Criação de problemas quadráticos binários (QuadraticProgram):
Cada ativo financeiro é representado como uma variável binária.

Função objetivo:
Maximização do retorno esperado (linear).
Minimização do risco via matriz de covariância (quadrática).
Combinação ponderada: -retorno + λ*risk, ajustável por lambda_risco.

Restrições do portfólio:
Número máximo de ativos selecionados (budget).
Outras restrições lineares podem ser facilmente adicionadas.

Conversão para QUBO:
Problema clássico → QUBO via QuadraticProgramToQubo.
QUBO é o formato necessário para rodar o QAOA.

Execução do QAOA:
Simulação em computador clássico (AerSimulator).
Otimizador clássico COBYLA para ajustar parâmetros do QAOA.
Resultado: ativos selecionados e valor ótimo da função objetivo.

Testes clássicos e gráficos:
Comparação com abordagem clássica (brute force ou heurística).
Visualização com matplotlib para mostrar ativos escolhidos:
Verde: selecionado
Cinza: não selecionado

🔹 Tecnologias utilizadas
Qiskit Optimization: QuadraticProgram, QuadraticProgramToQubo, MinimumEigenOptimizer.
Qiskit Algorithms: QAOA com COBYLA.

Simulador: AerSimulator.
Python Libraries: numpy, matplotlib.

🔹 Fluxo de execução
Definir ativos e retornos esperados.
Criar QuadraticProgram com variáveis binárias.
Adicionar função objetivo (retorno x risco).
Definir restrições (budget máximo).
Converter problema para QUBO.
Criar instância quântica (QuantumInstance) e rodar QAOA.
Obter resultados: ativos selecionados e valor da função objetivo.

Visualizar resultados com gráfico de barras.

Exemplo de saída:
Ativos selecionados pelo QAOA: ['ITUB4.SA', 'ABEV3.SA']
Valor ótimo da função objetivo: -0.00264
Ativos selecionados (clássico): ['ITUB4.SA', 'ABEV3.SA']
Gráfico de barras: mostra visualmente quais ativos foram escolhidos pelo algoritmo quântico.

🔹 O que esse projeto mostra
Aplicação prática de computação quântica em finanças.
Como transformar problemas financeiros em QUBOs binários.
Comparação entre resultados clássicos e quânticos.
Base para exploração de carteiras maiores, ajustes de risco e retornos, e algoritmos quânticos mais avançados.
