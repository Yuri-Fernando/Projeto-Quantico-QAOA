"""Scientific & Quantum Optimization Lab — módulos de otimização.

Duas trilhas, que NÃO se misturam em rankings (auditoria, "regra do protocolo"):

- **model_comparison** (v0.2.0): ``lp``, ``milp``, ``stochastic``, ``benders`` minimizam retorno +
  *shortfall*; ``qaoa`` minimiza média-variância. Mesma instância de dados, objetivos diferentes —
  compara FORMULAÇÕES de risco (``benchmarks/compare_methods.py``).
- **algorithm_benchmark** (v0.3.0): ``canonical_qubo`` define um único objetivo; ``classical_qubo``,
  ``heuristics`` e o QAOA de ``quantum/`` otimizam exatamente esse objetivo.
"""
