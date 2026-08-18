# Projeto Quântico — Otimização de Portfólio via QAOA

### Quantum Computing · Portfolio Optimization · Qiskit · QUBO · Financial Optimization

## Status

🟢 **Concluído — Projeto de portfólio / Computação Quântica Aplicada**

Projeto desenvolvido para demonstrar a aplicação de **algoritmos quânticos em otimização de portfólio**, utilizando o **QAOA (Quantum Approximate Optimization Algorithm)** e o framework Qiskit.

A solução modela a seleção de ativos como um problema de **otimização quadrática binária (QUBO)**, combinando retorno esperado, risco e restrições de orçamento para determinar uma composição de carteira.

---

## Sobre o Projeto

O problema de seleção de ativos é formulado como um problema de otimização no qual cada ativo financeiro é representado por uma variável binária:

```text
0 → ativo não selecionado
1 → ativo selecionado
```

O objetivo é encontrar uma combinação de ativos que equilibre:

- Retorno esperado;
- Risco da carteira;
- Quantidade máxima de ativos selecionados;
- Parâmetros de risco configuráveis.

Fluxo conceitual:

```text
Ativos + Retornos + Covariância
              ↓
       QuadraticProgram
              ↓
      Função Objetivo
       Retorno × Risco
              ↓
        Restrições
              ↓
        Conversão QUBO
              ↓
             QAOA
              ↓
      Seleção de Ativos
              ↓
   Comparação Clássica
              ↓
        Visualização
```

---

## Objetivo

Aplicar computação quântica a um problema financeiro de otimização combinatória, demonstrando como:

- Modelar seleção de ativos como problema binário;
- Representar risco por meio de uma matriz de covariância;
- Combinar retorno e risco em uma função objetivo;
- Converter o problema para QUBO;
- Resolver o QUBO utilizando QAOA;
- Comparar o resultado com uma abordagem clássica;
- Visualizar a composição do portfólio selecionado.

---

# Formulação do Problema

Cada ativo financeiro é representado por uma variável binária:

```text
xᵢ ∈ {0, 1}
```

A função objetivo combina retorno e risco.

A formulação utilizada pode ser representada de forma conceitual por:

```text
Objetivo = -Retorno + λ × Risco
```

onde:

- `Retorno` representa o retorno esperado;
- `Risco` é associado à matriz de covariância;
- `λ` (`lambda_risco`) controla a importância relativa do risco.

### Interpretação

```text
λ menor
   ↓
Maior peso no retorno

λ maior
   ↓
Maior penalização do risco
```

---

# Funcionalidades

## QuadraticProgram

Cada ativo é representado como variável binária dentro de um `QuadraticProgram`.

```text
Asset 1 → x₁ ∈ {0,1}
Asset 2 → x₂ ∈ {0,1}
Asset 3 → x₃ ∈ {0,1}
...
```

---

## Função Objetivo

A função combina:

### Retorno esperado

Componente linear responsável pela maximização do retorno esperado.

### Risco

Componente quadrática baseada na matriz de covariância dos ativos.

### Combinação

```text
-retorno + λ × risco
```

O parâmetro `lambda_risco` pode ser ajustado para explorar diferentes perfis de otimização.

---

## Restrições

A principal restrição implementada é o número máximo de ativos selecionados:

```text
Σ xᵢ ≤ budget
```

Isso representa um limite de ativos que podem compor a carteira.

A estrutura também permite adicionar outras restrições lineares conforme o problema evolua.

---

# Conversão para QUBO

O problema clássico é convertido para o formato necessário pelos algoritmos quânticos:

```text
QuadraticProgram
        ↓
QuadraticProgramToQubo
        ↓
QUBO
        ↓
QAOA
```

O QUBO representa o problema de otimização quadrática binária em uma formulação compatível com o algoritmo utilizado.

---

# QAOA

O projeto utiliza o **Quantum Approximate Optimization Algorithm (QAOA)** para buscar uma solução para o problema de seleção de ativos.

Fluxo:

```text
QUBO
 ↓
QAOA
 ↓
Quantum Circuit
 ↓
Classical Optimizer
 ↓
Candidate Solution
```

O processo utiliza:

- QAOA;
- Otimizador clássico COBYLA;
- Simulação através do AerSimulator.

---

# Execução Quântica

A implementação atual utiliza simulação em computador clássico por meio do:

```text
AerSimulator
```

Portanto, o projeto demonstra o algoritmo quântico em um ambiente simulado, não em hardware quântico físico.

---

# Otimização Clássica

O QAOA utiliza o **COBYLA** para otimização dos parâmetros variacionais.

O fluxo híbrido é:

```text
QAOA
  ↕
Quantum Simulation
  ↕
COBYLA
```

Essa combinação representa o caráter híbrido do algoritmo, alternando entre avaliação quântica e otimização clássica.

---

# Comparação Clássica

O projeto também compara a solução encontrada pelo algoritmo quântico com uma abordagem clássica.

Possibilidades utilizadas:

- Brute Force;
- Heurística clássica.

O objetivo é verificar se a seleção produzida pelo QAOA coincide ou se aproxima da solução encontrada pela abordagem clássica.

---

# Exemplo de Execução

Exemplo de resultado:

```text
Ativos selecionados pelo QAOA:
['ITUB4.SA', 'ABEV3.SA']

Valor ótimo da função objetivo:
-0.00264

Ativos selecionados pelo método clássico:
['ITUB4.SA', 'ABEV3.SA']
```

Neste cenário, a seleção obtida pelo método quântico coincide com a solução clássica apresentada no experimento.

---

# Visualização

O projeto utiliza **Matplotlib** para apresentar visualmente os ativos selecionados.

A visualização diferencia:

```text
Verde → ativo selecionado
Cinza → ativo não selecionado
```

O objetivo é facilitar a interpretação da carteira resultante do processo de otimização.

---

# Arquitetura do Pipeline

```text
Dados dos Ativos
      ↓
Retornos Esperados
      ↓
Matriz de Covariância
      ↓
QuadraticProgram
      ↓
Função Retorno + Risco
      ↓
Portfolio Constraints
      ↓
QuadraticProgramToQubo
      ↓
QAOA
      ↓
AerSimulator
      ↓
COBYLA
      ↓
Solução Ótima
      ↓
Classical Benchmark
      ↓
Visualização
```

---

# Tecnologias Utilizadas

| Categoria | Tecnologia |
|---|---|
| Linguagem | Python |
| Quantum Framework | Qiskit |
| Otimização | Qiskit Optimization |
| Algoritmo Quântico | QAOA |
| Formulação | QuadraticProgram |
| Conversão | QuadraticProgramToQubo |
| Otimizador | COBYLA |
| Simulador | AerSimulator |
| Dados / Computação | NumPy |
| Visualização | Matplotlib |

---

# Principais Componentes do Qiskit

### `QuadraticProgram`

Utilizado para representar o problema de otimização com variáveis binárias.

### `QuadraticProgramToQubo`

Realiza a transformação do problema para uma formulação QUBO.

### `MinimumEigenOptimizer`

Permite utilizar algoritmos variacionais/quânticos para resolver o problema de otimização.

### `QAOA`

Algoritmo utilizado para buscar uma solução aproximada para o problema combinatório.

### `AerSimulator`

Simulador utilizado para executar os circuitos quânticos no ambiente atual.

---

# Fluxo de Execução

```text
1. Definir ativos
        ↓
2. Definir retornos esperados
        ↓
3. Definir matriz de covariância
        ↓
4. Criar QuadraticProgram
        ↓
5. Criar função objetivo
        ↓
6. Adicionar restrição de budget
        ↓
7. Converter para QUBO
        ↓
8. Configurar QAOA
        ↓
9. Configurar COBYLA
        ↓
10. Executar no AerSimulator
        ↓
11. Obter ativos selecionados
        ↓
12. Calcular valor da função objetivo
        ↓
13. Executar abordagem clássica
        ↓
14. Comparar resultados
        ↓
15. Gerar visualização
```

---

# Estrutura Conceitual

```text
Portfolio Problem
       │
       ├── Assets
       ├── Expected Returns
       ├── Covariance Matrix
       ├── Budget
       └── Risk Parameter
              ↓
        Mathematical Model
              ↓
             QUBO
              ↓
        Quantum Optimization
              ↓
          Portfolio
```

---

# O que este projeto demonstra

- Aplicação de Computação Quântica em finanças;
- QAOA;
- Quantum Optimization;
- Formulação QUBO;
- Otimização combinatória;
- Modelagem de risco;
- Modelagem de retorno;
- Variáveis binárias;
- Qiskit Optimization;
- Simulação de circuitos quânticos;
- Otimização híbrida quântico-clássica;
- Comparação entre métodos quânticos e clássicos;
- Visualização de resultados financeiros.

---

# Casos de Uso

A arquitetura pode ser expandida para problemas como:

### Seleção de Ativos

Escolha de um subconjunto de ativos sob restrições.

### Otimização de Risco

Ajuste do peso do risco na função objetivo.

### Portfolio Constraints

Inclusão de novas restrições de composição de carteira.

### Otimização Combinatória

A mesma formulação pode ser adaptada para outros problemas financeiros e combinatórios.

---

# Como Executar

## Requisitos

- Python;
- Qiskit;
- Qiskit Optimization;
- Qiskit Aer;
- NumPy;
- Matplotlib.

## Instalação

```bash
pip install qiskit qiskit-optimization qiskit-aer numpy matplotlib
```

## Execução

Execute o script ou notebook principal do projeto conforme a estrutura do repositório.

O fluxo esperado é:

```text
Definir dados
    ↓
Criar QUBO
    ↓
Executar QAOA
    ↓
Comparar com método clássico
    ↓
Visualizar resultado
```

---

# Limitações

- A execução atual utiliza **AerSimulator**, não hardware quântico real;
- O número de ativos é limitado pela complexidade da simulação;
- A solução depende dos parâmetros utilizados no QAOA;
- O modelo atual utiliza uma formulação simplificada de seleção de ativos;
- A comparação clássica é realizada em um problema de escala compatível com o experimento;
- Os resultados não representam recomendação de investimento;
- O projeto possui finalidade experimental e educacional em computação quântica aplicada a finanças.

---

# Melhorias Futuras

- Execução em hardware quântico real;
- Testes em carteiras maiores;
- Comparação entre diferentes profundidades de QAOA;
- Ajuste automático dos parâmetros variacionais;
- Novas restrições de carteira;
- Otimização multiobjetivo;
- Inclusão de custos de transação;
- Limites por setor;
- Diversificação mínima;
- Comparação com outros algoritmos quânticos;
- Benchmark sistemático contra algoritmos clássicos;
- Estudos de escalabilidade;
- Integração com dados históricos da B3;
- Análise de estabilidade dos resultados.

---

# Status Final

🟢 **Concluído**

O projeto possui a implementação principal concluída, incluindo:

- ✅ Modelagem do problema como `QuadraticProgram`;
- ✅ Variáveis binárias para seleção de ativos;
- ✅ Função objetivo retorno × risco;
- ✅ Matriz de covariância;
- ✅ Restrição de budget;
- ✅ Conversão para QUBO;
- ✅ Execução com QAOA;
- ✅ Otimizador COBYLA;
- ✅ AerSimulator;
- ✅ Comparação com abordagem clássica;
- ✅ Visualização dos ativos selecionados;
- ✅ Exemplo de resultado documentado.

O projeto permanece como uma base experimental para exploração de **Quantum Computing, Quantum Optimization e aplicações financeiras**, especialmente em problemas de seleção e otimização combinatória.

---

# Licença

Consulte a licença definida no repositório.

---

# Autor

**Yuri Fernando Dubbern**

AI/ML Engineer · Quantum Computing · Machine Learning · Data Science · Optimization

[LinkedIn](https://www.linkedin.com/in/yuridubbern) · [GitHub](https://github.com/Yuri-Fernando) · [Lattes](http://lattes.cnpq.br/7151392692642166) · [Linktree](https://linktr.ee/yuri.f.dubbern)
