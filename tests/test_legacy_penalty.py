"""P0.5 — verifica a suspeita de dupla contagem da penalidade em ``legacy/v1/portfolio_qaoa.py``.

O arquivo legado importa ``qiskit.algorithms`` (removido no Qiskit >= 1.0), então não pode ser
importado. Extraímos apenas as funções ``build_instance``/``build_qubo`` via ``ast`` e as executamos
sem modificação.
"""
import ast
from pathlib import Path

import numpy as np
from qiskit_optimization import QuadraticProgram

from optimization.canonical_qubo import basis_matrix

LEGACY = Path(__file__).resolve().parent.parent / "legacy" / "v1" / "portfolio_qaoa.py"


def _load_legacy_functions():
    tree = ast.parse(LEGACY.read_text(encoding="utf-8"))
    funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name in {"build_instance", "build_qubo"}]
    namespace = {"np": np, "QuadraticProgram": QuadraticProgram}
    exec(compile(ast.Module(body=funcs, type_ignores=[]), str(LEGACY), "exec"), namespace)
    return namespace["build_instance"], namespace["build_qubo"]


def test_legacy_qubo_double_counts_off_diagonal_penalty():
    build_instance, build_qubo = _load_legacy_functions()
    tickers, mu, Sigma, budget, lam = build_instance()
    rho = 4.0
    qp = build_qubo(tickers, mu, Sigma, budget, lam, penalty=rho)

    for x in basis_matrix(len(tickers)).astype(float):
        legacy = qp.objective.evaluate(x)
        intended = -mu @ x + lam * x @ Sigma @ x + rho * (x.sum() - budget) ** 2
        cross = sum(x[i] * x[j] for i in range(len(x)) for j in range(i + 1, len(x)))
        # Diferença exata: o termo cruzado da penalidade entra com 4*rho em vez de 2*rho.
        assert np.isclose(legacy - intended, 2.0 * rho * cross, atol=1e-12)

    x_two = np.array([1.0, 1.0, 0.0])
    assert not np.isclose(qp.objective.evaluate(x_two),
                          -mu @ x_two + lam * x_two @ Sigma @ x_two)  # nem viável fica sem penalidade
