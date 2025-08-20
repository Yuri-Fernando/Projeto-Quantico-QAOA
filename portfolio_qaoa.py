import numpy as np
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit.algorithms import QAOA
from qiskit_aer import Aer
from qiskit.primitives import Estimator


def build_instance():
    # Ativos fictícios (PETR4, VALE3, ITUB4)
    tickers = ["PETR4", "VALE3", "ITUB4"]

    # retornos médios esperados (fictícios)
    mu = np.array([0.015, 0.012, 0.010])

    # matriz de covariância (fictícia e simétrica)
    Sigma = np.array([
        [0.04, 0.018, 0.012],
        [0.018, 0.035, 0.010],
        [0.012, 0.010, 0.030]
    ])

    budget = 2  # escolher 2 ativos
    lam = 0.5   # fator de aversão ao risco

    return tickers, mu, Sigma, budget, lam


def build_qubo(tickers, mu, Sigma, budget, lam, penalty=4.0):
    n = len(tickers)

    # Inicializa
    lin = -mu.copy()           # max mu^T x -> min -mu^T x
    Q = lam * Sigma.copy()     # risco
    const = 0

    # Penalidade do orçamento (sum x_i = budget)
    lin += penalty * (1 - 2 * budget)
    for i in range(n):
        for j in range(i+1, n):
            Q[i, j] += 2 * penalty
            Q[j, i] += 2 * penalty
    const += penalty * (budget**2)

    qp = QuadraticProgram("portfolio")
    for t in tickers:
        qp.binary_var(t)

    qp.minimize(quadratic=Q, linear=lin, constant=const)
    return qp


def solve_with_qaoa(qp, reps=2):
    backend = Aer.get_backend("aer_simulator_statevector")
    qaoa = QAOA(estimator=Estimator(), reps=reps)
    solver = MinimumEigenOptimizer(qaoa)
    result = solver.solve(qp)
    return result
