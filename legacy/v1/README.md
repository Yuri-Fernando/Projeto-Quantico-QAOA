# Legado v1 (agosto/2025) — preservado, NÃO executável no ambiente atual

Arquivos do rascunho original, movidos para cá com `git mv` na v0.3.0 (histórico git intacto).
Nenhum conteúdo foi alterado.

| Arquivo | Situação |
|---|---|
| `main.py`, `portfolio_qaoa.py` | Importam `qiskit.algorithms.QAOA` e `qiskit.primitives.Estimator` (API pré-1.0). Falham com Qiskit ≥ 1.0 — `python legacy/v1/main.py` **não funciona** no ambiente de `requirements.txt`. |
| `qaoa_portfolio.ipynb`, `qaoa_portfolio1.ipynb` | Notebooks originais (instância de 4 ativos). Não reexecutados. |
| `requirements.txt.txt` | Dependências sem pin do v1. |
| `qaoa_portfolio_mvp.zip`, `*.docx` | Scaffold inicial gerado na época. |
| `Captura de tela 2025-08-20 131417.jpg` | Saída histórica do notebook v1. |
| `projeto quântico.txt` | Notas pessoais de planejamento do rascunho. |

## Achado confirmado por teste: dupla contagem da penalidade em `build_qubo`

`portfolio_qaoa.build_qubo` soma `2*penalty` em `Q[i, j]` **e** em `Q[j, i]` de uma matriz que o
`QuadraticProgram` interpreta como `x^T Q x` completa — o termo cruzado da penalidade vira `4ρ x_i x_j`
em vez de `2ρ x_i x_j`. A energia resultante é `f(x) + ρ(Σx − k)² + 2ρ Σ_{i<j} x_i x_j`, não o QUBO
pretendido. `tests/test_legacy_penalty.py` extrai a função deste arquivo (sem importar o Qiskit antigo)
e verifica a diferença exata para todas as bitstrings.

O código atual usa a convenção triangular superior de `optimization/canonical_qubo.py`, que não tem
essa ambiguidade. Ponto de entrada canônico da versão atual: `python -m experiments.run` (ver README).
