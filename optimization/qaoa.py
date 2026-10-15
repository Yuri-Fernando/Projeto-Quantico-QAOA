"""QUBO/QAOA — formulação quadrática (média-variância) resolvida via QAOA.

Versão CONSERTADA e integrada à instância compartilhada do rascunho
original (``portfolio_qaoa.py`` na raiz, preservado intacto como v1).

Bug real encontrado e corrigido (API do Qiskit desatualizada, agosto/2025):

- ``from qiskit.algorithms import QAOA`` — módulo removido do Qiskit >= 1.0;
  QAOA migrou para o pacote separado ``qiskit_algorithms``.
- ``qiskit.primitives.Estimator`` (V1, BaseSamplerV1) é incompatível com a
  pipeline interna de ``qiskit_algorithms`` nesta combinação de versões
  (gera ``TypeError: Invalid circuits, expected Sequence[QuantumCircuit]``
  dentro de ``SamplingVQE``/``diagonal_estimator``). A correção foi trocar
  para o primitive V2 ``qiskit.primitives.StatevectorSampler``.
- O ambiente também tinha Qiskit <1.0 (``qiskit-terra`` 0.24) instalado
  junto com pacotes que exigiam Qiskit >=1.0, causando
  ``ImportError: Qiskit is installed in an invalid environment...``.
  Resolvido reinstalando um conjunto de versões consistente (ver
  ``requirements.txt``): qiskit 1.4.x + qiskit-aer + qiskit-optimization
  0.7 + qiskit-algorithms 0.4, sem qiskit-terra/qiskit-ibmq-provider soltos.

Nomenclatura (auditoria P0.2): ``StatevectorSampler`` calcula o estado ideal (sem ruído) e devolve
``default_shots=1024`` AMOSTRAS dele; o ``MinimumEigenOptimizer`` escolhe a melhor amostra. Isso é
"simulação ideal + amostragem finita", não "probabilidades exatas". Para probabilidades exatas,
viabilidade por amostra, QUBO exportado e mixers alternativos, use ``quantum.runner`` (v0.3.0).
Este módulo é mantido como está para a trilha ``model_comparison`` e para o teste da v0.2.0.

A restrição de orçamento (``sum x_i = budget``) é modelada como restrição
linear NATIVA do ``QuadraticProgram`` (não como penalidade manual como no
rascunho v1); o ``MinimumEigenOptimizer`` converte automaticamente para
QUBO (penalidade automática) antes de rodar o QAOA.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from qiskit.primitives import StatevectorSampler
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer

from .instance import PortfolioInstance


def build_quadratic_program(instance: PortfolioInstance) -> QuadraticProgram:
    """Constrói o QuadraticProgram de média-variância (mesmo risco quadrático
    usado em ``instance.quadratic_objective``), com a restrição de orçamento
    como restrição linear nativa (não penalidade manual)."""
    qp = QuadraticProgram("portfolio_mean_variance")
    for t in instance.tickers:
        qp.binary_var(t)

    linear = {instance.tickers[i]: float(-instance.mu[i]) for i in range(instance.n_assets)}

    quadratic = {}
    for i in range(instance.n_assets):
        for j in range(i, instance.n_assets):
            coef = instance.lam * instance.sigma[i, j] * (1.0 if i == j else 2.0)
            if coef != 0:
                quadratic[(instance.tickers[i], instance.tickers[j])] = float(coef)

    qp.minimize(linear=linear, quadratic=quadratic)
    qp.linear_constraint(
        linear={t: 1 for t in instance.tickers},
        sense="==",
        rhs=instance.budget,
        name="budget",
    )
    return qp


def solve_with_qaoa(
    instance: PortfolioInstance,
    reps: int = 2,
    maxiter: int = 200,
    seed: int = 42,
    initial_point: Optional[np.ndarray] = None,
) -> dict:
    qp = build_quadratic_program(instance)

    rng = np.random.default_rng(seed)
    if initial_point is None:
        initial_point = rng.uniform(0, 0.1, size=2 * reps)

    optimizer = COBYLA(maxiter=maxiter)
    qaoa = QAOA(
        sampler=StatevectorSampler(seed=seed),
        optimizer=optimizer,
        reps=reps,
        initial_point=initial_point,
    )
    solver = MinimumEigenOptimizer(qaoa)
    result = solver.solve(qp)

    x = np.array([result.variables_dict[t] for t in instance.tickers])
    return {
        "x": x,
        "objective": float(result.fval),
        "status": str(result.status),
        "raw_result": result,
    }
