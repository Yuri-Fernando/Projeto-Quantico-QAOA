"""Trilha ALGORITHM_BENCHMARK: clássicos exatos, heurísticas e QAOA no MESMO objetivo.

Atalho para ``experiments.run`` com a config E1 (ou outra passada em ``--config``).

    python -m benchmarks.fair_qubo_benchmark [--config experiments/configs/e1_ideal_qaoa.yaml] [--quick]
"""
from __future__ import annotations

import sys

from experiments.run import main

DEFAULT_CONFIG = "experiments/configs/e1_ideal_qaoa.yaml"

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--config" not in args:
        args = ["--config", DEFAULT_CONFIG, *args]
    main(args)
