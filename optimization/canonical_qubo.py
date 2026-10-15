"""Problema canônico, QUBO penalizado e Hamiltoniano de Ising — a base do benchmark justo.

Todo algoritmo do *algorithm benchmark* (enumeração, MILP linearizado, simulated annealing,
QAOA) otimiza a MESMA função definida aqui (ver ``docs/MATHEMATICAL_FORMULATION.md``):

    min  f(x) = x^T Q x + c        s.a.  sum_i x_i = k,   x in {0,1}^n

Convenções (fixas e testadas em ``tests/test_qubo_equivalence.py``):

- ``Q`` é **triangular superior**: ``Q[i, i]`` guarda o termo linear (``x_i^2 = x_i``) e ``Q[i, j]``
  (``i < j``) guarda o coeficiente COMPLETO de ``x_i x_j``. A parte inferior é zero. Isso elimina a
  ambiguidade de dupla contagem fora da diagonal (ver ``tests/test_legacy_penalty.py``).
- QUBO penalizado: ``E(x) = f(x) + rho * (sum_i x_i - k)^2``.
- Ising: ``x_i = (1 - z_i) / 2`` com ``z_i in {+1, -1}`` autovalor de ``Z_i`` (bit 0 <-> z = +1).
- Ordem de bits: o índice de base ``b`` tem ``x_i = (b >> i) & 1`` (little-endian, igual ao
  ``Statevector`` do Qiskit). Numa chave de contagem do Qiskit ``"b_{n-1}...b_0"``, ``x_i`` é o
  caractere na posição ``n - 1 - i``.
"""
from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from itertools import combinations
from typing import Optional

import numpy as np

OBJECTIVE_FAMILY = "card_quadratic_v1"


# --------------------------------------------------------------------------- bitstrings
def basis_matrix(n: int) -> np.ndarray:
    """Matriz ``(2^n, n)`` com ``X[b, i] = x_i`` do estado de base ``b`` (little-endian)."""
    if n > 24:
        raise ValueError(f"n={n} grande demais para enumeração completa (2^n estados)")
    idx = np.arange(2**n, dtype=np.int64)
    return ((idx[:, None] >> np.arange(n)) & 1).astype(np.int8)


def index_to_x(index: int, n: int) -> np.ndarray:
    return np.array([(index >> i) & 1 for i in range(n)], dtype=float)


def x_to_index(x: Sequence[float]) -> int:
    return int(sum(int(round(xi)) << i for i, xi in enumerate(x)))


def bitstring_to_x(bitstring: str) -> np.ndarray:
    """Chave de contagem do Qiskit (``"b_{n-1}...b_0"``) -> vetor ``x`` com ``x_i`` do qubit ``i``."""
    bits = bitstring.replace(" ", "")
    return np.array([int(c) for c in reversed(bits)], dtype=float)


def x_to_bitstring(x: Sequence[float]) -> str:
    return "".join(str(int(round(xi))) for xi in reversed(list(x)))


# --------------------------------------------------------------------------- problema
@dataclass(frozen=True)
class CardinalityProblem:
    """``min x^T Q x + c  s.a.  sum x = k`` com ``Q`` triangular superior."""

    name: str
    domain: str
    labels: tuple[str, ...]
    Q: np.ndarray
    constant: float
    k: int
    metadata: dict = field(default_factory=dict, compare=False)

    def __post_init__(self):
        Q = np.asarray(self.Q, dtype=float)
        n = len(self.labels)
        if Q.shape != (n, n):
            raise ValueError(f"Q deve ser {n}x{n}, recebido {Q.shape}")
        if not np.all(np.isfinite(Q)) or not np.isfinite(self.constant):
            raise ValueError("Q e constante devem ser finitos")
        if np.any(np.abs(np.tril(Q, -1)) > 0):
            raise ValueError("Q deve ser triangular superior (convenção sem dupla contagem)")
        if not (1 <= self.k <= n):
            raise ValueError(f"cardinalidade k={self.k} fora de [1, {n}]")
        object.__setattr__(self, "Q", Q)
        object.__setattr__(self, "labels", tuple(self.labels))

    # -- básicos
    @property
    def n(self) -> int:
        return len(self.labels)

    @property
    def n_feasible(self) -> int:
        from math import comb

        return comb(self.n, self.k)

    def evaluate(self, x: Sequence[float]) -> float:
        x = np.asarray(x, dtype=float)
        return float(x @ self.Q @ x + self.constant)

    def evaluate_many(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=float)
        return np.einsum("bi,ij,bj->b", X, self.Q, X) + self.constant

    def is_feasible(self, x: Sequence[float]) -> bool:
        x = np.asarray(x, dtype=float)
        binary = np.all(np.isclose(x, 0.0) | np.isclose(x, 1.0))
        return bool(binary and int(round(x.sum())) == self.k)

    def feasible_selections(self) -> Iterable[np.ndarray]:
        for combo in combinations(range(self.n), self.k):
            x = np.zeros(self.n)
            x[list(combo)] = 1.0
            yield x

    # -- identidade
    @property
    def instance_hash(self) -> str:
        h = hashlib.sha256()
        h.update(self.domain.encode())
        h.update(str(self.k).encode())
        h.update(np.round(self.Q, 12).astype(np.float64).tobytes())
        h.update(np.float64(round(self.constant, 12)).tobytes())
        return h.hexdigest()

    @property
    def objective_id(self) -> str:
        return f"{self.domain}:{OBJECTIVE_FAMILY}:n{self.n}k{self.k}:{self.instance_hash[:12]}"

    # -- penalidade
    def safe_penalty(self) -> float:
        """Penalidade que GARANTE que o mínimo de ``E`` seja viável.

        Para ``x`` inviável, ``(sum x - k)^2 >= 1``; logo ``E(x) >= f_min + rho``. Como
        ``f_max - f_min <= sum |Q_ij|`` (cada termo varia em ``[min(0,Q_ij), max(0,Q_ij)]``),
        ``rho > sum |Q_ij|`` implica ``E(x_inviável) > f_max >= f*``.
        """
        return float(np.abs(self.Q).sum() * (1.0 + 1e-3) + 1e-9)

    def penalized_qubo(self, rho: Optional[float] = None) -> QUBO:
        rho = self.safe_penalty() if rho is None else float(rho)
        if rho < 0:
            raise ValueError("penalidade deve ser >= 0")
        n, k = self.n, self.k
        Q = self.Q.copy()
        # rho (sum x - k)^2 = rho [ sum_i (1 - 2k) x_i + 2 sum_{i<j} x_i x_j + k^2 ]
        Q[np.diag_indices(n)] += rho * (1 - 2 * k)
        Q[np.triu_indices(n, 1)] += 2.0 * rho
        return QUBO(Q=Q, offset=self.constant + rho * k * k, rho=rho, k=k, labels=self.labels)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "domain": self.domain,
            "objective_id": self.objective_id,
            "instance_hash": self.instance_hash,
            "labels": list(self.labels),
            "k": self.k,
            "Q_upper": self.Q.tolist(),
            "constant": self.constant,
            "metadata": self.metadata,
        }


def problem_from_quadratic(
    linear: Sequence[float],
    quadratic: np.ndarray,
    k: int,
    labels: Sequence[str],
    name: str,
    domain: str,
    constant: float = 0.0,
    metadata: Optional[dict] = None,
) -> CardinalityProblem:
    """Converte ``f(x) = linear^T x + x^T M x + c`` (``M`` qualquer) para a forma triangular superior."""
    M = np.asarray(quadratic, dtype=float)
    n = len(labels)
    Q = np.zeros((n, n))
    Q[np.diag_indices(n)] = np.asarray(linear, dtype=float) + np.diag(M)
    iu = np.triu_indices(n, 1)
    Q[iu] = M[iu] + M.T[iu]
    return CardinalityProblem(
        name=name, domain=domain, labels=tuple(labels), Q=Q, constant=float(constant), k=int(k),
        metadata=dict(metadata or {}),
    )


# --------------------------------------------------------------------------- QUBO
@dataclass(frozen=True)
class QUBO:
    Q: np.ndarray  # triangular superior, já com a penalidade
    offset: float
    rho: float
    k: int
    labels: tuple[str, ...]

    @property
    def n(self) -> int:
        return self.Q.shape[0]

    def evaluate(self, x: Sequence[float]) -> float:
        x = np.asarray(x, dtype=float)
        return float(x @ self.Q @ x + self.offset)

    def energies(self) -> np.ndarray:
        """``E`` para os ``2^n`` estados de base, indexados little-endian."""
        X = basis_matrix(self.n).astype(float)
        return np.einsum("bi,ij,bj->b", X, self.Q, X) + self.offset

    def to_ising(self) -> IsingHamiltonian:
        n = self.n
        h = np.zeros(n)
        J = np.zeros((n, n))
        offset = self.offset
        for i in range(n):
            q = self.Q[i, i]
            offset += q / 2.0
            h[i] -= q / 2.0
        for i in range(n):
            for j in range(i + 1, n):
                q = self.Q[i, j]
                if q == 0.0:
                    continue
                offset += q / 4.0
                h[i] -= q / 4.0
                h[j] -= q / 4.0
                J[i, j] += q / 4.0
        return IsingHamiltonian(h=h, J=J, offset=offset)

    def to_dict(self) -> dict:
        ising = self.to_ising()
        nz = int(np.count_nonzero(np.triu(self.Q, 1)))
        return {
            "rho": self.rho,
            "offset": self.offset,
            "Q_upper": self.Q.tolist(),
            "n_linear_terms": int(np.count_nonzero(np.diag(self.Q))),
            "n_quadratic_terms": nz,
            "ising": ising.to_dict(),
        }


@dataclass(frozen=True)
class IsingHamiltonian:
    """``H = sum_i h_i Z_i + sum_{i<j} J_ij Z_i Z_j + offset`` (``J`` triangular superior)."""

    h: np.ndarray
    J: np.ndarray
    offset: float

    @property
    def n(self) -> int:
        return len(self.h)

    def energy_z(self, z: Sequence[float]) -> float:
        z = np.asarray(z, dtype=float)
        return float(self.h @ z + z @ self.J @ z + self.offset)

    def energies(self) -> np.ndarray:
        Z = 1.0 - 2.0 * basis_matrix(self.n).astype(float)
        return Z @ self.h + np.einsum("bi,ij,bj->b", Z, self.J, Z) + self.offset

    def edges(self, tol: float = 0.0) -> list[tuple[int, int, float]]:
        n = self.n
        return [(i, j, float(self.J[i, j])) for i in range(n) for j in range(i + 1, n) if abs(self.J[i, j]) > tol]

    def to_sparse_pauli_op(self, include_offset: bool = True):
        from qiskit.quantum_info import SparsePauliOp

        n = self.n
        terms = []
        for i in range(n):
            if self.h[i] != 0.0:
                terms.append(("Z", [i], float(self.h[i])))
        for i, j, w in self.edges():
            terms.append(("ZZ", [i, j], w))
        if include_offset and self.offset != 0.0:
            terms.append(("", [], float(self.offset)))
        if not terms:
            terms.append(("", [], 0.0))
        return SparsePauliOp.from_sparse_list(terms, num_qubits=n).simplify(atol=0.0)

    def to_dict(self) -> dict:
        return {"h": self.h.tolist(), "J_upper": self.J.tolist(), "offset": self.offset,
                "n_zz_terms": len(self.edges())}


# --------------------------------------------------------------------------- análise de penalidade
def critical_penalty(problem: CardinalityProblem) -> float:
    """Menor ``rho`` a partir do qual o estado fundamental do QUBO é viável (por enumeração).

    ``E`` tem mínimo viável sse ``f(x) + rho d(x)^2 > f*`` para todo ``x`` inviável, com
    ``d(x) = sum x - k``; logo ``rho_c = max(0, max_inviável (f* - f(x)) / d(x)^2)``.
    """
    X = basis_matrix(problem.n).astype(float)
    f = problem.evaluate_many(X)
    d = X.sum(axis=1) - problem.k
    feasible = d == 0
    f_star = f[feasible].min()
    ratios = (f_star - f[~feasible]) / d[~feasible] ** 2
    return float(max(0.0, ratios.max()))
