"""Simulador exato e vetorizado do QAOA com custo diagonal (regime IDEAL, sem ruído).

Implementa exatamente o mesmo unitário de ``quantum.ansatz.build_qaoa_circuit`` (paridade testada
contra ``qiskit.quantum_info.Statevector`` em ``tests/test_ansatz.py``), mas aplica a camada de custo
como uma multiplicação elemento a elemento ``exp(-iγ E(z)/s)`` e o mixer qubit a qubit. Custa
``O(p · n · 2^n)`` por avaliação, contra montar/simular um circuito a cada passo do otimizador.

Devolve probabilidades EXATAS da evolução ideal. Amostragem finita é uma etapa separada
(``sample_counts``) — as duas coisas nunca são confundidas nos relatórios (auditoria P0.2).
"""
from __future__ import annotations

import numpy as np

from optimization.canonical_qubo import IsingHamiltonian, basis_matrix, x_to_bitstring

from .ansatz import hamiltonian_scale, ring_pairs

STATEVECTOR_BYTES_PER_AMPLITUDE = 16  # complex128


class ExactQAOASimulator:
    def __init__(self, ising: IsingHamiltonian, p: int, mixer: str = "x", init: str = "plus", k: int | None = None):
        self.n = ising.n
        self.p = p
        self.mixer = mixer
        self.init = init
        self.k = k
        self.scale = hamiltonian_scale(ising)
        self.diag = (ising.energies() - ising.offset) / self.scale  # fase global removida (igual ao circuito)
        weights = basis_matrix(self.n).sum(axis=1)
        if init == "plus":
            self.psi0 = np.full(2**self.n, 2 ** (-self.n / 2), dtype=complex)
        elif init == "dicke":
            mask = weights == k
            self.psi0 = np.where(mask, 1.0 / np.sqrt(mask.sum()), 0.0).astype(complex)
        else:
            raise ValueError(init)
        self._pair_index: list[tuple[np.ndarray, np.ndarray]] = []
        if mixer == "xy_ring":
            idx = np.arange(2**self.n)
            for i, j in ring_pairs(self.n):
                differ = ((idx >> i) & 1) != ((idx >> j) & 1)
                src = idx[differ]
                self._pair_index.append((src, src ^ (1 << i) ^ (1 << j)))

    def statevector(self, params: np.ndarray) -> np.ndarray:
        params = np.asarray(params, dtype=float)
        gammas, betas = params[: self.p], params[self.p:]
        psi = self.psi0.copy()
        n = self.n
        for g, b in zip(gammas, betas):
            psi *= np.exp(-1j * g * self.diag)
            if self.mixer == "x":
                c, s = np.cos(b), -1j * np.sin(b)
                for q in range(n):
                    v = psi.reshape(2 ** (n - 1 - q), 2, 2**q)
                    a0, a1 = v[:, 0, :].copy(), v[:, 1, :].copy()
                    v[:, 0, :] = c * a0 + s * a1
                    v[:, 1, :] = s * a0 + c * a1
            else:
                c, s = np.cos(b), -1j * np.sin(b)
                for src, dst in self._pair_index:
                    new = psi.copy()
                    new[src] = c * psi[src] + s * psi[dst]
                    psi = new
        return psi

    def probabilities(self, params: np.ndarray) -> np.ndarray:
        prob = np.abs(self.statevector(params)) ** 2
        return prob / prob.sum()


def sample_counts(probabilities: np.ndarray, shots: int, rng: np.random.Generator) -> dict[str, int]:
    """Amostragem finita (multinomial) de ``shots`` a partir de probabilidades exatas."""
    n = int(np.log2(len(probabilities)))
    draws = rng.multinomial(shots, probabilities)
    nz = np.flatnonzero(draws)
    X = ((nz[:, None] >> np.arange(n)) & 1)
    return {x_to_bitstring(x): int(draws[b]) for b, x in zip(nz, X)}
