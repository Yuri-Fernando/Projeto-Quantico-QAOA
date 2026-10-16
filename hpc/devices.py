"""Detecção REAL de dispositivos (auditoria P2.1): nada é presumido.

Distingue três fatos independentes, que costumam ser confundidos:

1. existe uma GPU NVIDIA no host (``nvidia-smi``);
2. o ``qiskit-aer`` instalado foi compilado com CUDA (``AerSimulator().available_devices()``);
3. o experimento de fato rodou em GPU (registrado por execução, em ``ExecutionResult.device``).

No Windows, os wheels do ``qiskit-aer`` publicados no PyPI são somente CPU (``qiskit-aer-gpu`` é
distribuído para Linux), então (1) pode ser verdadeiro com (2) falso.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
from functools import lru_cache
from typing import Optional


@lru_cache(maxsize=1)
def aer_available_devices() -> tuple:
    try:
        from qiskit_aer import AerSimulator

        return tuple(AerSimulator().available_devices())
    except Exception as exc:  # pragma: no cover - ambiente sem Aer
        return (f"error: {exc}",)


def aer_gpu_available() -> bool:
    return "GPU" in aer_available_devices()


def nvidia_gpus(timeout: float = 10.0) -> Optional[list]:
    exe = shutil.which("nvidia-smi") or (r"C:\Windows\System32\nvidia-smi.exe" if os.name == "nt" else None)
    if not exe or not os.path.exists(exe):
        return None
    try:
        out = subprocess.run([exe, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=timeout, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    gpus = []
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 3:
            gpus.append({"name": parts[0], "memory_total": parts[1], "driver": parts[2]})
    return gpus


def host_info() -> dict:
    info = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "processor": platform.processor() or platform.machine(),
        "cpu_count_logical": os.cpu_count(),
        "ram_total_gb": None,
    }
    try:
        import psutil

        info["ram_total_gb"] = round(psutil.virtual_memory().total / 2**30, 2)
        info["cpu_count_physical"] = psutil.cpu_count(logical=False)
    except ImportError:
        pass
    return info


def detect_devices() -> dict:
    gpus = nvidia_gpus()
    aer = aer_available_devices()
    gpu_in_aer = "GPU" in aer
    if gpu_in_aer:
        gpu_status = "available"
    elif gpus:
        gpu_status = "host_has_nvidia_gpu_but_qiskit_aer_build_is_cpu_only"
    else:
        gpu_status = "no_gpu_detected"
    return {
        "host": host_info(),
        "nvidia_gpus": gpus,
        "aer_available_devices": list(aer),
        "aer_gpu_available": gpu_in_aer,
        "gpu_status": gpu_status,
        "qiskit_ibm_runtime_installed": _module_installed("qiskit_ibm_runtime"),
    }


def _module_installed(name: str) -> bool:
    import importlib.util

    return importlib.util.find_spec(name) is not None
