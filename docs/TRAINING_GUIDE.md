# Mini-guia (20–30 min): QUBO, QAOA e como interpretar "speedup" com responsabilidade

Roteiro de capacitação usando este repositório. Cada bloco tem um comando que roda offline.

## 1. Do problema ao QUBO (5 min)

- Problema: escolher `k` de `n` itens minimizando `f(x) = xᵀQx + c` (`docs/MATHEMATICAL_FORMULATION.md`).
- Restrições viram penalidade: `E(x) = f(x) + ρ(Σx − k)²`. ρ grande garante viabilidade do mínimo,
  mas domina a escala e achata a paisagem; ρ pequeno deixa o mínimo inviável.
- Pergunta para a turma: por que não deixar como MILP? Resposta: para hardware quântico atual não há
  "restrição" nativa — só energia. No clássico, MILP é a ferramenta certa.

```bash
python -m experiments.run --config experiments/configs/e0_equivalence.yaml --quick
```

## 2. QAOA em uma página (5 min)

- Estado inicial → `p` camadas de (custo `e^{−iγH}`, mixer `e^{−iβB}`) → medir → otimizador clássico
  ajusta `γ, β`.
- Mixer X: explora tudo, inclusive soluções inviáveis. Mixer XY + estado de Dicke: só visita soluções
  com exatamente `k` uns — viabilidade por construção, ao custo de mais portas de dois qubits.
- Saída é uma **distribuição**. A solução é a melhor amostra viável, não "o resultado do solver".

## 3. Lógico × físico: profundidade, conectividade e SWAPs (5 min)

- O QUBO de portfólio é denso: todo par de qubits interage. Num chip com conectividade em linha ou
  heavy-hex, o compilador insere SWAPs — cada um custa 3 CX.
- Comparar `two_qubit_gates_logical` × `two_qubit_gates_physical` e `swap_count`:

```bash
python -m experiments.run --config experiments/configs/e2_hardware_aware.yaml --quick
```

## 4. Amostragem e ruído (5 min)

- Shots finitos ⇒ estimativas com barra de erro (IC de Wilson para proporções).
- Ruído de leitura quebra a preservação de cardinalidade do mixer XY; ruído de porta degrada a
  concentração de probabilidade. O protocolo mede isso no MESMO circuito.

```bash
python -m experiments.demo --n 6 --mixer xy_ring --p 2 --backend fake --out demo.html
```

## 5. CPU, GPU, QPU: o que foi realmente usado? (3 min)

- `hpc.devices.detect_devices()` separa "há GPU no host" de "o simulador usa GPU" e de "este run
  rodou em GPU". Nesta máquina a GPU existe mas o Aer instalado é só CPU.
- QPU exige opt-in explícito, credenciais fora do Git e orçamento; sem isso o experimento registra
  `not_executed`/`BLOCKED_BY_CONFIGURATION`.

## 6. Interpretação responsável (5 min)

Checklist antes de dizer "o quântico foi melhor":

1. O baseline clássico otimiza **a mesma** função com **as mesmas** restrições?
2. A comparação usa o mesmo orçamento (amostras, tempo total — não só o tempo do solver)?
3. `P(ótimo)` supera o sorteio aleatório de soluções viáveis com o mesmo número de amostras?
4. Há múltiplas seeds, ICs e remoção de pseudo-réplicas?
5. O tempo de simulação clássica do circuito foi confundido com tempo de QPU?
6. A conclusão vale fora das instâncias testadas? (Normalmente não.)

Resposta deste laboratório, hoje: nas instâncias medidas, métodos clássicos encontram o ótimo com
certificado em milissegundos; o QAOA é objeto de estudo, não ferramenta de produção
(`docs/adr/ADR-001-quando-nao-usar-qaoa.md`).
