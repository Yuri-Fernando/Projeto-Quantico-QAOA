"""Backends fake e regimes de ruído locais (auditoria P1.2, experimento E3).

IMPORTANTE (``docs/HARDWARE_LIMITATIONS.md``): nenhum backend daqui é hardware real.

- ``generic_line_<n>`` / ``generic_heavyhex_d3`` / ``generic_all_to_all_<n>``: ``GenericBackendV2``
  com topologia escolhida e taxas de erro SINTÉTICAS sorteadas por seed — servem para estudar
  conectividade/roteamento, não para prever fidelidade de um dispositivo.
- ``fake27_snapshot``: ``Fake27QPulseV1`` (Qiskit 1.4), um snapshot FIXO de propriedades de um
  dispositivo heavy-hex de 27 qubits empacotado na biblioteca. Não é calibração atual; está
  deprecated e sai no Qiskit 2.0.

Regimes: ``ideal`` (sem ruído), ``readout`` (só erro de medição), ``depolarizing`` (só portas),
``readout+depolarizing`` e ``backend`` (modelo derivado das propriedades do backend fake).
"""
from __future__ import annotations

import hashlib
import json
import warnings
from typing import Optional

from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import CouplingMap
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

REGIMES = ("ideal", "readout", "depolarizing", "readout+depolarizing", "backend")
DEFAULT_NOISE = {"p1": 1e-3, "p2": 1e-2, "p_meas": 2e-2}


def get_fake_backend(name: str, seed: int = 7):
    """Backends fake por nome: ``generic_line_<n>``, ``generic_all_to_all_<n>``, ``generic_heavyhex_d3``,
    ``fake27_snapshot``."""
    if name == "fake27_snapshot":
        from qiskit.providers import BackendV2Converter
        from qiskit.providers.fake_provider import Fake27QPulseV1

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            return BackendV2Converter(Fake27QPulseV1())
    if name == "generic_heavyhex_d3":
        return GenericBackendV2(num_qubits=19, coupling_map=CouplingMap.from_heavy_hex(3), seed=seed)
    if name.startswith("generic_line_"):
        n = int(name.rsplit("_", 1)[1])
        return GenericBackendV2(num_qubits=n, coupling_map=CouplingMap.from_line(n), seed=seed)
    if name.startswith("generic_all_to_all_"):
        n = int(name.rsplit("_", 1)[1])
        return GenericBackendV2(num_qubits=n, coupling_map=CouplingMap.from_full(n), seed=seed)
    raise ValueError(f"backend fake desconhecido: {name}")


def build_noise_model(regime: str, params: Optional[dict] = None, backend=None) -> Optional[NoiseModel]:
    if regime not in REGIMES:
        raise ValueError(f"regime em {REGIMES}")
    if regime == "ideal":
        return None
    if regime == "backend":
        if backend is None:
            raise ValueError("regime 'backend' exige um backend fake")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            return NoiseModel.from_backend(backend)
    prm = {**DEFAULT_NOISE, **(params or {})}
    nm = NoiseModel(basis_gates=["rz", "sx", "x", "cx"])
    if "depolarizing" in regime:
        nm.add_all_qubit_quantum_error(depolarizing_error(prm["p1"], 1), ["sx", "x"])
        nm.add_all_qubit_quantum_error(depolarizing_error(prm["p2"], 2), ["cx"])
    if "readout" in regime:
        p = prm["p_meas"]
        nm.add_all_qubit_readout_error(ReadoutError([[1 - p, p], [p, 1 - p]]))
    return nm


def _strip_ids(obj):
    """O ``to_dict`` do Aer inclui um ``id`` aleatório (uuid) por ``QuantumError``; não é conteúdo."""
    if isinstance(obj, dict):
        return {k: _strip_ids(v) for k, v in obj.items() if not (k == "id" and obj.get("type") == "qerror")}
    if isinstance(obj, list):
        return [_strip_ids(v) for v in obj]
    return obj


def noise_model_hash(noise_model: Optional[NoiseModel]) -> Optional[str]:
    if noise_model is None:
        return None
    content = _strip_ids(noise_model.to_dict(serializable=True))
    payload = json.dumps(content, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()
