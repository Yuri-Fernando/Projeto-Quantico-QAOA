"""Adaptadores de execução com resultado unificado (``ExecutionResult``).

- ``ExactStatevectorBackend``: probabilidades exatas (``Statevector``) + amostragem multinomial.
- ``AerBackend``: Qiskit Aer em CPU ou GPU (somente se ``available_devices()`` listar GPU), ideal,
  com regime de ruído e/ou topologia de backend fake.
- ``IBMQPUBackend``: hardware IBM Quantum, só com ``allow_qpu=True``, credenciais externas e
  orçamento de shots/jobs. Nunca usado em testes/CI.
"""
from .aer import AerBackend, ExactStatevectorBackend, GPUUnavailable
from .base import BackendAdapter, ExecutionResult, library_versions
from .ibm_qpu import IBMQPUBackend, QPUBudget, QPUNotAllowed, QPUUnavailable

__all__ = [
    "AerBackend", "BackendAdapter", "ExactStatevectorBackend", "ExecutionResult", "GPUUnavailable",
    "IBMQPUBackend", "QPUBudget", "QPUNotAllowed", "QPUUnavailable", "library_versions",
]
