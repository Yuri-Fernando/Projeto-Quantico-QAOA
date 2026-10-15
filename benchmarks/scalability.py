"""Curvas de escala (E4): tempo e memória de clássicos exatos × simulação do QAOA.

    python -m benchmarks.scalability [--quick]
"""
from __future__ import annotations

import sys

from experiments.run import main

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--config" not in args:
        args = ["--config", "experiments/configs/e4_scalability.yaml", *args]
    main(args)
