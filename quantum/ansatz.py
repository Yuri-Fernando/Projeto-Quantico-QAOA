"""Circuitos QAOA explícitos (portas visíveis, sem ``PauliEvolutionGate``).

Duas políticas de viabilidade (auditoria P0.5, formulação 3):

- ``mixer="x"``, ``init="plus"``: QAOA padrão sobre o QUBO PENALIZADO. Visita todo o espaço
  ``{0,1}^n``; a viabilidade depende da penalidade ``rho``.
- ``mixer="xy_ring"``, ``init="dicke"``: estado de Dicke ``|D^n_k>`` + mixer XY em anel. Cada porta
  ``RXX(β)·RYY(β) = exp(-iβ(XX+YY)/2)`` preserva o peso de Hamming, então TODA amostra ideal tem
  ``sum x = k``; o custo é ``f`` sem penalidade. Preço: preparação de Dicke e ``2n`` portas de dois
  qubits extras por camada de mixer — medido em ``quantum.transpilation``.

Camada de custo: ``exp(-iγ (H - offset)/s)`` com ``RZ(2γh_i/s)`` e ``RZZ(2γJ_ij/s)``, onde ``s`` é a
escala (maior |coeficiente|) para manter γ = O(1). O offset só altera a fase global.
"""
from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.circuit.library import RYGate

from optimization.canonical_qubo import IsingHamiltonian

MIXERS = ("x", "xy_ring")
INITS = ("plus", "dicke")


def hamiltonian_scale(ising: IsingHamiltonian) -> float:
    coeffs = np.concatenate([np.abs(ising.h), np.abs(ising.J[np.triu_indices(ising.n, 1)])])
    s = float(coeffs.max()) if coeffs.size else 0.0
    return s if s > 0 else 1.0


def ring_pairs(n: int) -> list[tuple[int, int]]:
    if n < 2:
        return []
    if n == 2:
        return [(0, 1)]
    return [(i, (i + 1) % n) for i in range(n)]


def _scs(qc: QuantumCircuit, top: int, k: int) -> None:
    """Split & Cyclic Shift ``SCS_{top,k}`` (Bärtschi & Eidenbenz, 2019) — qubits 1-indexados."""
    q = lambda paper_index: paper_index - 1  # noqa: E731
    n = top
    qc.cx(q(n - 1), q(n))
    qc.cry(2 * np.arccos(np.sqrt(1 / n)), q(n), q(n - 1))
    qc.cx(q(n - 1), q(n))
    for ell in range(2, k + 1):
        qc.cx(q(n - ell), q(n))
        ccry = RYGate(2 * np.arccos(np.sqrt(ell / n))).control(2)
        qc.append(ccry, [q(n), q(n - ell + 1), q(n - ell)])
        qc.cx(q(n - ell), q(n))


def dicke_state_circuit(n: int, k: int) -> QuantumCircuit:
    """Prepara ``|D^n_k>`` (superposição uniforme dos estados de peso ``k``) deterministicamente."""
    if not 0 <= k <= n:
        raise ValueError("0 <= k <= n")
    qc = QuantumCircuit(n, name=f"dicke_{n}_{k}")
    for i in range(n - k, n):
        qc.x(i)
    if k in (0, n):
        return qc
    for top in range(n, k, -1):
        _scs(qc, top, k)
    for top in range(k, 1, -1):
        _scs(qc, top, top - 1)
    return qc


def build_qaoa_circuit(ising: IsingHamiltonian, p: int, mixer: str = "x", init: str = "plus",
                       k: int | None = None, measure: bool = False) -> QuantumCircuit:
    """Circuito parametrizado com ``γ_0..γ_{p-1}`` e ``β_0..β_{p-1}`` (nesta ordem em ``parameters``)."""
    if mixer not in MIXERS or init not in INITS:
        raise ValueError(f"mixer em {MIXERS}, init em {INITS}")
    if mixer == "xy_ring" and init != "dicke":
        raise ValueError("mixer XY exige estado inicial de peso k (init='dicke')")
    if init == "dicke" and k is None:
        raise ValueError("init='dicke' exige k")
    n = ising.n
    scale = hamiltonian_scale(ising)
    gammas = ParameterVector("γ", p)
    betas = ParameterVector("β", p)
    qc = QuantumCircuit(n, name=f"qaoa_p{p}_{mixer}")
    if init == "plus":
        qc.h(range(n))
    else:
        qc.compose(dicke_state_circuit(n, k), inplace=True)
    edges = ising.edges()
    for layer in range(p):
        for i in range(n):
            if ising.h[i] != 0.0:
                qc.rz(2 * gammas[layer] * float(ising.h[i]) / scale, i)
        for i, j, w in edges:
            qc.rzz(2 * gammas[layer] * w / scale, i, j)
        if mixer == "x":
            qc.rx(2 * betas[layer], range(n))
        else:
            for i, j in ring_pairs(n):
                qc.rxx(betas[layer], i, j)
                qc.ryy(betas[layer], i, j)
    qc.metadata = {"p": p, "mixer": mixer, "init": init, "k": k, "hamiltonian_scale": scale}
    if measure:
        qc.measure_all()
    return qc


def ordered_parameters(circuit: QuantumCircuit) -> list:
    """Parâmetros na ordem ``[γ_0..γ_{p-1}, β_0..β_{p-1}]`` (o Qiskit ordena por nome)."""
    gam = sorted((prm for prm in circuit.parameters if prm.name.startswith("γ")), key=lambda x: x.index)
    bet = sorted((prm for prm in circuit.parameters if prm.name.startswith("β")), key=lambda x: x.index)
    return gam + bet


def bind(circuit: QuantumCircuit, params: np.ndarray) -> QuantumCircuit:
    return circuit.assign_parameters(dict(zip(ordered_parameters(circuit), np.asarray(params, dtype=float))))
