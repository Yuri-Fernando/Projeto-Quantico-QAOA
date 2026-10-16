"""Estimativa de recursos de simulação/execução (auditoria P1.3).

Memória de estado: ``16 · 2^n`` bytes (statevector complex128) e ``16 · 4^n`` (matriz densidade),
ANTES de overheads do simulador. São limites inferiores teóricos, não medições.
"""
from __future__ import annotations

from math import comb


def statevector_bytes(n: int) -> int:
    return 16 * 2**n


def density_matrix_bytes(n: int) -> int:
    return 16 * 4**n


def estimate_resources(n: int, k: int, p: int, mixer: str, n_zz_terms: int, n_z_terms: int | None = None) -> dict:
    n_z = n if n_z_terms is None else n_z_terms
    if mixer == "x":
        mixer_1q, mixer_2q = n, 0
    else:
        pairs = 0 if n < 2 else (1 if n == 2 else n)
        mixer_1q, mixer_2q = 0, 2 * pairs  # RXX + RYY por par do anel
    return {
        "num_qubits": n,
        "feasible_states": comb(n, k),
        "hilbert_dim": 2**n,
        "statevector_bytes": statevector_bytes(n),
        "density_matrix_bytes": density_matrix_bytes(n),
        "logical_two_qubit_gates_per_layer": n_zz_terms + mixer_2q,
        "logical_two_qubit_gates_total": p * (n_zz_terms + mixer_2q),
        "logical_one_qubit_rotations_total": p * (n_z + mixer_1q),
        "note": "contagem lógica, antes de transpilation; Dicke (mixer XY) acrescenta portas de preparação",
    }
