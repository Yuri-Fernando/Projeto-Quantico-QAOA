# Formulação matemática canônica

Base de todo o *algorithm benchmark*: clássico e quântico otimizam **a mesma função** com **as mesmas
restrições**. Implementação: `optimization/canonical_qubo.py`; paridade testada em
`tests/test_qubo_equivalence.py` e no experimento E0.

## 1. Problema

Variáveis `x_i ∈ {0,1}`, `i = 0..n−1`; selecionar exatamente `k`.

```
min  f(x) = Σ_i Q_ii x_i + Σ_{i<j} Q_ij x_i x_j + c        s.a.  Σ_i x_i = k
```

`Q` é **triangular superior**: a diagonal guarda os termos lineares (para binários, `x_i² = x_i`) e
`Q_ij` (`i<j`) guarda o coeficiente **completo** de `x_i x_j`. A parte inferior é zero e o construtor
rejeita qualquer outra convenção — é isso que elimina a dupla contagem fora da diagonal.

`objective_id = <domínio>:card_quadratic_v1:n<n>k<k>:<hash>` e `instance_hash = sha256(domínio, k, Q, c)`
identificam o objetivo em cada registro de experimento.

### 1.1 Portfólio (média-variância)

`f(x) = −μᵀx + λ xᵀΣx`, com `Σ` simétrica PSD. Logo `Q_ii = −μ_i + λΣ_ii` e `Q_ij = 2λΣ_ij` (`i<j`).
`Σ` densa ⇒ grafo de custo **completo** (`n(n−1)/2` termos quadráticos).

### 1.2 Seleção de tarefas por turno (E7)

`f(x) = −Σ_j w_j x_j + Σ_{i<j} α s_ij x_i x_j`, onde `s_ij` é o número de recursos compartilhados pelas
ordens `i` e `j`. Grafo de custo **esparso** (só pares em conflito; ~30% dos pares nas instâncias geradas).

## 2. QUBO penalizado (QAOA padrão, mixer X)

```
E(x) = f(x) + ρ (Σ_i x_i − k)²
     = f(x) + ρ [ (1 − 2k) Σ_i x_i + 2 Σ_{i<j} x_i x_j + k² ]
```

Na forma triangular: `Q_ii += ρ(1−2k)`, `Q_ij += 2ρ` (`i<j`), `offset = c + ρk²`. Tudo exportado em
`QUBO.to_dict()` (`rho`, `offset`, termos lineares/quadráticos e o Ising correspondente).

**Penalidade segura** (`safe_penalty`). Para `x` inviável, `(Σx − k)² ≥ 1`, então
`E(x) ≥ f_min + ρ`. Como `f_max − f_min ≤ Σ_{i≤j} |Q_ij|`, escolher `ρ > Σ|Q_ij|` garante
`E(x_inviável) > f_max ≥ f*`: o estado fundamental é viável e ótimo.

**Penalidade crítica** (`critical_penalty`, por enumeração). O fundamental é viável sse
`f(x) + ρ d(x)² > f*` para todo `x` inviável, com `d(x) = Σx − k`:
`ρ_c = max(0, max_{x inviável} (f* − f(x)) / d(x)²)`.

Medido no E0 (50 instâncias): `ρ_c / ρ_seguro` tem média **0,036** no portfólio e **0,098** no
escalonamento, com máximo **0,41** — a penalidade
segura é muito conservadora. O E1c mostra o custo disso: ela domina a escala do Hamiltoniano e achata
a paisagem do objetivo.

### 2.1 Achado no legado

`legacy/v1/portfolio_qaoa.py::build_qubo` soma `2ρ` em `Q[i,j]` **e** em `Q[j,i]` de uma matriz que o
`QuadraticProgram` lê como `xᵀQx` completa: o termo cruzado vira `4ρ`. Confirmado por teste para todas
as bitstrings: `E_legado − E_pretendido = 2ρ Σ_{i<j} x_i x_j`.

## 3. Ising

`x_i = (1 − z_i)/2`, `z_i ∈ {+1, −1}` (autovalor de `Z_i`; bit 0 ↔ `z = +1`).

```
H = Σ_i h_i Z_i + Σ_{i<j} J_ij Z_i Z_j + offset_ising
Q_ii x_i      →  offset += Q_ii/2,  h_i −= Q_ii/2
Q_ij x_i x_j  →  offset += Q_ij/4,  h_i −= Q_ij/4,  h_j −= Q_ij/4,  J_ij += Q_ij/4
```

`to_sparse_pauli_op()` gera o `SparsePauliOp` (incluindo o offset como termo `I`). Para todos os
`2^n` estados: `diag(H) = E(x)` com erro ≤ 4,4e-16 (E0).

**Ordem de bits.** Índice de base `b` ↔ `x_i = (b >> i) & 1` (little-endian, igual ao `Statevector`).
Numa chave de contagem do Qiskit `"b_{n−1}…b_0"`, `x_i` é o caractere na posição `n−1−i`.

## 4. Baseline clássico equivalente (MILP linearizado)

HiGHS não resolve MIQP; o produto binário é linearizado por McCormick, exato para `x` binário:

```
y_ij ≤ x_i,   y_ij ≤ x_j,   y_ij ≥ x_i + x_j − 1,   y_ij ≥ 0        (para cada i<j com Q_ij ≠ 0)
min  Σ_i Q_ii x_i + Σ_{i<j} Q_ij y_ij + c     s.a.  Σ_i x_i = k
```

A relaxação LP do mesmo modelo (`x, y ∈ [0,1]`) é um limite inferior válido — verificado (T18).
Para n pequeno, a **enumeração** das `C(n,k)` seleções é o oráculo de referência.

## 5. Viabilidade preservada (mixer XY + Dicke)

- Estado inicial `|D^n_k⟩` (superposição uniforme dos estados de peso de Hamming `k`), preparado de
  forma determinística (Bärtschi & Eidenbenz, 2019) com CX, CRY e CCRY — validado contra o vetor exato.
- Mixer em anel: para cada par `(i, i+1 mod n)`, `RXX(β)·RYY(β) = exp(−iβ(XX+YY)/2)`, que só troca
  amplitudes entre `|01⟩` e `|10⟩` ⇒ peso de Hamming preservado exatamente.
- Custo: `f` **sem penalidade** (`ρ = 0`). No portfólio o grafo continua completo; no escalonamento
  fica esparso. Preço: portas de preparação de Dicke + `2n` portas de dois qubits por camada de mixer.

As duas políticas **não** implementam o mesmo ansatz; são comparadas como alternativas de projeto.

## 6. Camada de custo e escala

O circuito aplica `exp(−iγ(H − offset)/s)` com `RZ(2γh_i/s)` e `RZZ(2γJ_ij/s)`, onde `s` é o maior
`|h_i|, |J_ij|` (registrado como `hamiltonian_scale`). O offset só altera a fase global; `s` é apenas
uma reparametrização de `γ`.
