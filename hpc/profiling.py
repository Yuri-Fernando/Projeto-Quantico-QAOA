"""Medição de tempo por estágio e memória (auditoria §7: tempo TOTAL, não só o do solver)."""
from __future__ import annotations

import sys
import time
import tracemalloc
from contextlib import contextmanager
from typing import Optional


class StageTimer:
    def __init__(self):
        self.times: dict[str, float] = {}

    @contextmanager
    def stage(self, name: str):
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self.times[name] = self.times.get(name, 0.0) + time.perf_counter() - t0

    def add(self, name: str, seconds: Optional[float]) -> None:
        if seconds is not None:
            self.times[name] = self.times.get(name, 0.0) + float(seconds)


@contextmanager
def traced_memory(enabled: bool = True):
    """Pico de alocações Python/NumPy (``tracemalloc``) durante o bloco. Não vê memória do C++ do Aer."""
    box = {"peak_traced_mb": None}
    if not enabled:
        yield box
        return
    was_tracing = tracemalloc.is_tracing()
    if not was_tracing:
        tracemalloc.start()
    tracemalloc.reset_peak()
    try:
        yield box
    finally:
        box["peak_traced_mb"] = tracemalloc.get_traced_memory()[1] / 2**20
        if not was_tracing:
            tracemalloc.stop()


def process_peak_rss_mb() -> Optional[float]:
    """Pico de memória residente do PROCESSO desde o início (inclui Aer/C++); não é por execução."""
    try:
        import psutil

        info = psutil.Process().memory_info()
        peak = getattr(info, "peak_wset", None)  # Windows
        if peak is not None:
            return peak / 2**20
    except ImportError:
        pass
    if sys.platform != "win32":
        import resource

        kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return kb / 1024 if sys.platform != "darwin" else kb / 2**20
    return None
