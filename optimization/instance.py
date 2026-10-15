"""Instância compartilhada do problema de otimização de portfólio.

Todos os métodos deste projeto (LP, MILP, estocástico, Benders, QUBO/QAOA)
resolvem a MESMA instância definida aqui, para permitir comparação justa
entre eles. Os dados (tickers, retornos esperados, covariância) são os
mesmos ativos fictícios do rascunho original (``portfolio_qaoa.py``):
PETR4, VALE3, ITUB4.

Dois modelos de risco coexistem de propósito, e isso é documentado:

- **Risco quadrático (média-variância / Markowitz):** ``x^T Sigma x``.
  É o risco "nativo" de QUBO/QAOA (precisa de termos quadráticos).
- **Risco de shortfall por cenários (linear):** espera de déficit abaixo
  de uma meta de retorno ``tau``, calculada sobre cenários simulados.
  É o risco usado por LP/MILP/estocástico/Benders, porque esses métodos
  (exceto quando o solver aceita QP) são formulados como programas
  LINEARES — exigência explícita da auditoria para a categoria "LP".

O benchmark (``benchmarks/compare_methods.py``) avalia TODAS as soluções
finais nas DUAS métricas, para que a comparação entre métodos seja honesta
mesmo quando eles otimizam objetivos formalmente diferentes.
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from itertools import combinations

import numpy as np

TICKERS: list[str] = ["PETR4", "VALE3", "ITUB4"]

# Retornos médios esperados (fictícios, mesmos do rascunho original)
MU = np.array([0.015, 0.012, 0.010])

# Matriz de covariância (fictícia, simétrica e positiva semidefinida)
SIGMA = np.array(
    [
        [0.04, 0.018, 0.012],
        [0.018, 0.035, 0.010],
        [0.012, 0.010, 0.030],
    ]
)

BUDGET = 2  # escolher exatamente 2 dos 3 ativos
LAMBDA_RISK = 0.5  # aversão ao risco

N_SCENARIOS = 8
SCENARIO_SEED = 42

TAU_TARGET = 0.0  # retorno mínimo desejado da carteira (meta de shortfall)
HEDGE_COST = 0.3  # custo por unidade de hedge no recurso de 2º estágio
HEDGE_CAP = 0.10  # limite superior de hedge disponível por cenário


@dataclass(frozen=True)
class PortfolioInstance:
    tickers: list[str]
    mu: np.ndarray
    sigma: np.ndarray
    budget: int
    lam: float
    scenarios: np.ndarray  # shape (S, n): retornos simulados por cenário
    probabilities: np.ndarray  # shape (S,)
    tau: float
    hedge_cost: float
    hedge_cap: float

    def __post_init__(self):
        validate_instance(self)

    @property
    def n_assets(self) -> int:
        return len(self.tickers)

    @property
    def n_scenarios(self) -> int:
        return len(self.probabilities)

    def feasible_selections(self) -> Iterator[np.ndarray]:
        """Gera, por força bruta, todas as seleções binárias viáveis (sum x = budget)."""
        n = self.n_assets
        for combo in combinations(range(n), self.budget):
            x = np.zeros(n)
            x[list(combo)] = 1.0
            yield x

    def quadratic_objective(self, x: np.ndarray) -> float:
        """-mu^T x + lam * x^T Sigma x (minimização). Métrica nativa do QUBO/QAOA."""
        x = np.asarray(x, dtype=float)
        return float(-self.mu @ x + self.lam * (x @ self.sigma @ x))

    def scenario_returns(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        return self.scenarios @ x

    def expected_shortfall_metric(self, x: np.ndarray) -> float:
        """E[max(0, tau - retorno_cenário)]: métrica de risco LINEAR usada para
        comparar LP/MILP/estocástico/Benders de forma consistente."""
        r = self.scenario_returns(x)
        shortfall = np.maximum(0.0, self.tau - r)
        return float(self.probabilities @ shortfall)

    def to_problem(self):
        """Problema canônico (``optimization.canonical_qubo``) do objetivo média-variância.

        ``f(x) = -mu^T x + lam x^T Sigma x`` com ``sum x = budget`` — exatamente
        ``quadratic_objective``; é o objetivo comum do *algorithm benchmark*.
        """
        from .canonical_qubo import problem_from_quadratic

        return problem_from_quadratic(
            linear=-self.mu,
            quadratic=self.lam * self.sigma,
            k=self.budget,
            labels=self.tickers,
            name=f"portfolio_n{self.n_assets}_k{self.budget}",
            domain="portfolio",
            metadata={"lam": self.lam},
        )


def validate_instance(inst: PortfolioInstance, psd_tol: float = 1e-10) -> None:
    """Valida dimensões, simetria, PSD de Sigma, cardinalidade e probabilidades (T16)."""
    n = len(inst.tickers)
    mu = np.asarray(inst.mu, dtype=float)
    sigma = np.asarray(inst.sigma, dtype=float)
    if mu.shape != (n,):
        raise ValueError(f"mu deve ter shape ({n},), recebido {mu.shape}")
    if sigma.shape != (n, n):
        raise ValueError(f"Sigma deve ter shape ({n},{n}), recebido {sigma.shape}")
    if not (np.all(np.isfinite(mu)) and np.all(np.isfinite(sigma))):
        raise ValueError("mu e Sigma devem ser finitos")
    if not np.allclose(sigma, sigma.T, atol=1e-12):
        raise ValueError("Sigma deve ser simétrica")
    min_eig = float(np.linalg.eigvalsh(sigma).min())
    if min_eig < -psd_tol:
        raise ValueError(f"Sigma não é positiva semidefinida (menor autovalor {min_eig:.3e})")
    if not (1 <= inst.budget <= n):
        raise ValueError(f"budget={inst.budget} fora de [1, {n}]")
    if inst.lam < 0:
        raise ValueError("lam (aversão ao risco) deve ser >= 0")
    p = np.asarray(inst.probabilities, dtype=float)
    if np.any(p < 0) or not np.isclose(p.sum(), 1.0):
        raise ValueError("probabilidades de cenário devem ser >= 0 e somar 1")
    if np.asarray(inst.scenarios).shape != (len(p), n):
        raise ValueError("scenarios deve ter shape (S, n)")


def generate_portfolio_instance(
    n: int,
    k: int | None = None,
    seed: int = 0,
    lam: float = LAMBDA_RISK,
    n_factors: int = 3,
    n_scenarios: int = N_SCENARIOS,
) -> PortfolioInstance:
    """Instância sintética reprodutível com ``n`` ativos (E01).

    ``Sigma = B B^T + diag(d)`` (modelo de fatores) é PSD por construção; as magnitudes imitam a
    instância original (variâncias ~0,03–0,05, retornos ~0,5–2%). ``k = floor(n/2)`` por padrão.
    Dados 100% sintéticos — não representam ativos reais.
    """
    if n < 2:
        raise ValueError("n deve ser >= 2")
    k = n // 2 if k is None else int(k)
    rng = np.random.default_rng(seed)
    mu = rng.uniform(0.005, 0.02, size=n)
    B = rng.normal(0.0, 0.08, size=(n, n_factors))
    d = rng.uniform(0.01, 0.02, size=n)
    sigma = B @ B.T + np.diag(d)
    sigma = (sigma + sigma.T) / 2.0
    scenarios = rng.multivariate_normal(mu, sigma, size=n_scenarios)
    return PortfolioInstance(
        tickers=[f"A{i:02d}" for i in range(n)],
        mu=mu,
        sigma=sigma,
        budget=k,
        lam=lam,
        scenarios=scenarios,
        probabilities=np.full(n_scenarios, 1.0 / n_scenarios),
        tau=TAU_TARGET,
        hedge_cost=HEDGE_COST,
        hedge_cap=HEDGE_CAP,
    )


def build_instance(n_scenarios: int = N_SCENARIOS, seed: int = SCENARIO_SEED) -> PortfolioInstance:
    """Constrói a instância padrão do projeto, com cenários reprodutíveis (seed fixa)."""
    rng = np.random.default_rng(seed)
    scenarios = rng.multivariate_normal(MU, SIGMA, size=n_scenarios)
    probabilities = np.full(n_scenarios, 1.0 / n_scenarios)
    return PortfolioInstance(
        tickers=list(TICKERS),
        mu=MU.copy(),
        sigma=SIGMA.copy(),
        budget=BUDGET,
        lam=LAMBDA_RISK,
        scenarios=scenarios,
        probabilities=probabilities,
        tau=TAU_TARGET,
        hedge_cost=HEDGE_COST,
        hedge_cap=HEDGE_CAP,
    )


def brute_force_optimum(instance: PortfolioInstance):
    """Busca exaustiva no espaço discreto viável (métrica quadrática = QUBO/QAOA).

    Usado como "verdade fundamental" nos testes, válido porque o espaço de
    seleções viáveis é pequeno (C(n, budget)).
    """
    best_x, best_val = None, np.inf
    for x in instance.feasible_selections():
        val = instance.quadratic_objective(x)
        if val < best_val:
            best_val, best_x = val, x
    return best_x, best_val
