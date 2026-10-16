"""Segundo domínio (E7): seleção de tarefas para um turno com conflito de recursos compartilhados.

Cenário industrial sintético: há ``n`` ordens de produção pendentes e o próximo turno comporta
exatamente ``k`` delas. Cada ordem ``j`` tem prioridade ``w_j`` (ganho de antecipá-la) e usa um
subconjunto de ``m`` recursos escassos (ferramentas, operadores especializados, estações). Duas
ordens no mesmo turno que disputam ``s_ij`` recursos geram custo de contenção ``alpha * s_ij``
(espera/setup adicional).

    min  f(x) = - sum_j w_j x_j + sum_{i<j} alpha * s_ij x_i x_j     s.a.  sum_j x_j = k

É a MESMA família canônica do portfólio (``CardinalityProblem``), então enumeração, MILP
linearizado, heurísticas e QAOA se aplicam sem mudança e com objetivo idêntico. Diferença
estrutural relevante para hardware: a matriz de conflito é ESPARSA (só pares que compartilham
recurso), enquanto a covariância do portfólio é densa — o que muda o número de portas ZZ e de
SWAPs quando a penalidade não é usada (mixer XY). Dados 100% sintéticos (seed registrada).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .canonical_qubo import CardinalityProblem, problem_from_quadratic


@dataclass(frozen=True)
class ShiftSchedulingInstance:
    jobs: tuple
    priority: np.ndarray  # w_j
    resource_usage: np.ndarray  # (n, m) binária
    alpha: float
    k: int
    seed: int

    @property
    def n(self) -> int:
        return len(self.jobs)

    @property
    def shared_resources(self) -> np.ndarray:
        R = self.resource_usage.astype(float)
        S = R @ R.T
        np.fill_diagonal(S, 0.0)
        return S

    def conflict_density(self) -> float:
        S = self.shared_resources
        n = self.n
        return float(np.count_nonzero(np.triu(S, 1)) / (n * (n - 1) / 2)) if n > 1 else 0.0

    def to_problem(self) -> CardinalityProblem:
        conflict = np.triu(self.alpha * self.shared_resources, 1)
        return problem_from_quadratic(
            linear=-self.priority,
            quadratic=conflict,
            k=self.k,
            labels=self.jobs,
            name=f"shift_scheduling_n{self.n}_k{self.k}",
            domain="shift_scheduling",
            metadata={"alpha": self.alpha, "seed": self.seed, "conflict_density": self.conflict_density()},
        )


def generate_shift_scheduling_instance(n: int, k: int | None = None, seed: int = 0, n_resources: int | None = None,
                                       usage_prob: float = 0.25, alpha: float = 0.6) -> ShiftSchedulingInstance:
    if n < 2:
        raise ValueError("n >= 2")
    k = n // 2 if k is None else int(k)
    if not 1 <= k <= n:
        raise ValueError("1 <= k <= n")
    rng = np.random.default_rng(seed)
    m = n_resources or max(3, n // 2)
    usage = (rng.random((n, m)) < usage_prob).astype(np.int8)
    for j in range(n):  # toda ordem usa ao menos um recurso
        if usage[j].sum() == 0:
            usage[j, rng.integers(m)] = 1
    priority = rng.uniform(0.5, 1.5, size=n)
    return ShiftSchedulingInstance(jobs=tuple(f"J{j:02d}" for j in range(n)), priority=priority,
                                   resource_usage=usage, alpha=alpha, k=k, seed=seed)
