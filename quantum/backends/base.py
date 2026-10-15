"""Contrato comum dos backends (auditoria §6: objeto consistente por execução)."""
from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from importlib import metadata
from typing import Optional

from qiskit import QuantumCircuit, qasm2


def library_versions() -> dict[str, Optional[str]]:
    out = {}
    for pkg in ("qiskit", "qiskit-aer", "qiskit-algorithms", "qiskit-optimization", "qiskit-ibm-runtime",
                "numpy", "scipy", "pyomo", "highspy"):
        try:
            out[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            out[pkg] = None
    return out


def circuit_hash(circuit: QuantumCircuit) -> str:
    try:
        text = qasm2.dumps(circuit)
    except Exception:  # portas sem representação QASM2 (ex.: controladas customizadas)
        parts = []
        for ins in circuit.data:
            params = tuple(round(float(p), 12) for p in ins.operation.params if hasattr(p, "__float__"))
            qubits = tuple(circuit.find_bit(q).index for q in ins.qubits)
            parts.append(f"{ins.operation.name}{params}{qubits}")
        text = "|".join(parts)
    return hashlib.sha256(text.encode()).hexdigest()


@dataclass
class ExecutionResult:
    backend_type: str  # ideal_exact | aer_ideal | aer_noisy | aer_fake_backend | ibm_qpu | ibm_qpu_dry_run
    backend_name: str
    is_real_hardware: bool
    device: str  # CPU | GPU | QPU
    shots: int
    counts: dict[str, int]
    status: str  # completed | dry_run | failed | timeout | cancelled
    seed: Optional[int] = None
    circuit_hash: Optional[str] = None
    physical_qubits: Optional[list[int]] = None
    noise_regime: Optional[str] = None
    noise_model_hash: Optional[str] = None
    transpile_metrics: dict = field(default_factory=dict)
    elapsed: dict[str, float] = field(default_factory=dict)
    job_id: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    solver_versions: dict = field(default_factory=library_versions)
    metadata: dict = field(default_factory=dict)

    def to_dict(self, include_counts: bool = True) -> dict:
        d = asdict(self)
        if not include_counts:
            d.pop("counts")
        return d


class BackendAdapter(ABC):
    backend_type: str = "abstract"
    is_real_hardware: bool = False

    @abstractmethod
    def run(self, circuit: QuantumCircuit, shots: int, seed: Optional[int] = None) -> ExecutionResult:
        """Executa um circuito LÓGICO com medições finais e devolve contagens no layout lógico."""
