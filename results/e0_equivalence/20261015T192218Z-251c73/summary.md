# e0_equivalence — resumo gerado de `records.jsonl`

- run_id: `20261015T192218Z-251c73` · kind: `equivalence` · track: `algorithm_benchmark`
- commit: `fc936b306ae185aba003a6ff2933b24877c54ceb` (working tree suja: False)
- config_hash: `c331de7a6c479809` · registros: 50 · tempo de parede: 4.8s · modo quick: False
- Python 3.10.8 · qiskit 1.4.6 · qiskit-aer 0.17.2 · GPU: host_has_nvidia_gpu_but_qiskit_aer_build_is_cpu_only
- Toda execução quântica aqui é SIMULAÇÃO em CPU (`is_real_hardware=false`), salvo indicação explícita.
**Paridade:** 50/50 instâncias passaram em todas as checagens.

| domain | n | k | instance_seed | max_abs_f_vs_original | max_abs_qubo_vs_f_plus_penalty | max_abs_ising_vs_qubo | max_abs_pauli_vs_qubo | abs_diff_milp_vs_enumeration | lp_le_milp | critical_penalty | safe_penalty | qubo_ground_state_is_optimal | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| portfolio | 3 | 1 | 0 | 0.0000 | 6.94e-18 | 6.94e-18 | 6.94e-18 | 0.0000 | sim | 4.29e-04 | 0.0393 | sim | sim |
| portfolio | 3 | 1 | 1 | 4.34e-18 | 3.47e-18 | 3.47e-18 | 1.39e-17 | 0.0000 | sim | 0.0000 | 0.0211 | sim | sim |
| portfolio | 3 | 1 | 2 | 1.39e-17 | 1.39e-17 | 1.39e-17 | 2.78e-17 | 0.0000 | sim | 0.0000 | 0.0782 | sim | sim |
| portfolio | 3 | 1 | 3 | 3.47e-18 | 3.47e-18 | 1.39e-17 | 2.78e-17 | 0.0000 | sim | 0.0027 | 0.1082 | sim | sim |
| portfolio | 3 | 1 | 4 | 3.47e-18 | 1.39e-17 | 0.0000 | 0.0000 | 0.0000 | sim | 0.0105 | 0.0319 | sim | sim |
| portfolio | 4 | 2 | 0 | 1.39e-17 | 8.33e-17 | 2.78e-17 | 5.55e-17 | 0.0000 | sim | 0.0000 | 0.1154 | sim | sim |
| portfolio | 4 | 2 | 1 | 6.94e-18 | 4.86e-17 | 5.55e-17 | 2.78e-17 | 3.47e-18 | sim | 0.0038 | 0.0430 | sim | sim |
| portfolio | 4 | 2 | 2 | 6.94e-18 | 6.94e-17 | 5.55e-17 | 5.55e-17 | 1.73e-18 | sim | 0.0000 | 0.0680 | sim | sim |
| portfolio | 4 | 2 | 3 | 1.56e-17 | 5.55e-17 | 8.33e-17 | 5.55e-17 | 0.0000 | sim | 3.30e-04 | 0.1222 | sim | sim |
| portfolio | 4 | 2 | 4 | 6.94e-18 | 1.11e-16 | 5.55e-17 | 5.55e-17 | 0.0000 | sim | 0.0057 | 0.1027 | sim | sim |
| portfolio | 5 | 2 | 0 | 1.39e-17 | 1.11e-16 | 1.11e-16 | 4.44e-16 | 1.73e-18 | sim | 0.0018 | 0.1602 | sim | sim |
| portfolio | 5 | 2 | 1 | 8.67e-18 | 5.55e-17 | 5.55e-17 | 5.55e-17 | 3.47e-18 | sim | 0.0044 | 0.0463 | sim | sim |
| portfolio | 5 | 2 | 2 | 6.94e-18 | 2.22e-16 | 1.11e-16 | 1.11e-16 | 0.0000 | sim | 0.0051 | 0.0784 | sim | sim |
| portfolio | 5 | 2 | 3 | 1.39e-17 | 1.11e-16 | 1.11e-16 | 2.22e-16 | 0.0000 | sim | 0.0000 | 0.1643 | sim | sim |
| portfolio | 5 | 2 | 4 | 1.39e-17 | 1.11e-16 | 1.11e-16 | 1.11e-16 | 0.0000 | sim | 0.0100 | 0.1376 | sim | sim |
| portfolio | 6 | 3 | 0 | 1.39e-17 | 6.66e-16 | 6.66e-16 | 6.11e-16 | 0.0000 | sim | 0.0000 | 0.2008 | sim | sim |
| portfolio | 6 | 3 | 1 | 1.04e-17 | 1.39e-16 | 2.22e-16 | 2.22e-16 | 3.47e-18 | sim | 9.13e-04 | 0.0705 | sim | sim |
| portfolio | 6 | 3 | 2 | 1.04e-17 | 1.39e-16 | 2.78e-16 | 3.33e-16 | 6.94e-18 | sim | 0.0031 | 0.0810 | sim | sim |
| portfolio | 6 | 3 | 3 | 2.78e-17 | 9.44e-16 | 9.44e-16 | 9.44e-16 | 0.0000 | sim | 0.0000 | 0.2407 | sim | sim |
| portfolio | 6 | 3 | 4 | 2.17e-17 | 5.27e-16 | 5.00e-16 | 5.00e-16 | 3.47e-18 | sim | 0.0035 | 0.1837 | sim | sim |
| portfolio | 8 | 4 | 0 | 4.16e-17 | 1.55e-15 | 1.67e-15 | 1.67e-15 | 3.47e-18 | sim | 0.0032 | 0.2864 | sim | sim |
| portfolio | 8 | 4 | 1 | 2.08e-17 | 1.33e-15 | 1.11e-15 | 1.11e-15 | 0.0000 | sim | 0.0076 | 0.2495 | sim | sim |
| portfolio | 8 | 4 | 2 | 2.26e-17 | 1.33e-15 | 1.33e-15 | 1.33e-15 | 0.0000 | sim | 0.0036 | 0.2244 | sim | sim |
| portfolio | 8 | 4 | 3 | 4.86e-17 | 1.03e-15 | 1.44e-15 | 1.44e-15 | 3.47e-18 | sim | 0.0034 | 0.2763 | sim | sim |
| portfolio | 8 | 4 | 4 | 5.55e-17 | 1.72e-15 | 1.67e-15 | 1.67e-15 | 6.25e-17 | sim | 3.76e-04 | 0.3789 | sim | sim |
| shift_scheduling | 3 | 1 | 0 | 0.0000 | 1.78e-15 | 1.78e-15 | 1.78e-15 | 0.0000 | sim | 1.3159 | 3.1792 | sim | sim |
| shift_scheduling | 3 | 1 | 1 | 0.0000 | 4.44e-16 | 8.88e-16 | 4.44e-16 | 0.0000 | sim | 1.0381 | 3.7251 | sim | sim |
| shift_scheduling | 3 | 1 | 2 | 2.22e-16 | 3.55e-15 | 3.55e-15 | 8.88e-16 | 0.0000 | sim | 0.3326 | 4.4494 | sim | sim |
| shift_scheduling | 3 | 1 | 3 | 1.11e-16 | 4.44e-16 | 8.88e-16 | 8.88e-16 | 0.0000 | sim | 0.2912 | 4.3260 | sim | sim |
| shift_scheduling | 3 | 1 | 4 | 4.44e-16 | 1.78e-15 | 8.88e-16 | 4.44e-16 | 0.0000 | sim | 0.9305 | 3.9138 | sim | sim |
| shift_scheduling | 4 | 2 | 0 | 0.0000 | 2.66e-15 | 3.55e-15 | 3.55e-15 | 0.0000 | sim | 0.6757 | 4.4065 | sim | sim |
| shift_scheduling | 4 | 2 | 1 | 4.44e-16 | 2.66e-15 | 2.22e-15 | 2.22e-15 | 0.0000 | sim | 0.2032 | 4.8840 | sim | sim |
| shift_scheduling | 4 | 2 | 2 | 4.44e-16 | 3.55e-15 | 3.55e-15 | 3.55e-15 | 0.0000 | sim | 0.5693 | 5.8986 | sim | sim |
| shift_scheduling | 4 | 2 | 3 | 4.44e-16 | 5.33e-15 | 3.55e-15 | 3.55e-15 | 0.0000 | sim | 0.4868 | 7.1186 | sim | sim |
| shift_scheduling | 4 | 2 | 4 | 4.44e-16 | 7.11e-15 | 4.00e-15 | 4.00e-15 | 0.0000 | sim | 1.2889 | 5.7175 | sim | sim |
| shift_scheduling | 5 | 2 | 0 | 4.44e-16 | 5.33e-15 | 3.55e-15 | 1.42e-14 | 0.0000 | sim | 0.5283 | 6.4618 | sim | sim |
| shift_scheduling | 5 | 2 | 1 | 8.88e-16 | 4.88e-15 | 7.11e-15 | 7.11e-15 | 0.0000 | sim | 0.7623 | 5.6053 | sim | sim |
| shift_scheduling | 5 | 2 | 2 | 8.88e-16 | 1.42e-14 | 1.07e-14 | 1.42e-14 | 0.0000 | sim | 0.6873 | 7.4828 | sim | sim |
| shift_scheduling | 5 | 2 | 3 | 4.44e-16 | 3.55e-15 | 7.11e-15 | 7.11e-15 | 0.0000 | sim | 0.5485 | 6.8300 | sim | sim |
| shift_scheduling | 5 | 2 | 4 | 8.88e-16 | 1.42e-14 | 1.42e-14 | 1.07e-14 | 0.0000 | sim | 0.8290 | 7.0703 | sim | sim |
| shift_scheduling | 6 | 3 | 0 | 4.44e-16 | 2.84e-14 | 9.77e-15 | 8.88e-15 | 0.0000 | sim | 0.3227 | 7.9164 | sim | sim |
| shift_scheduling | 6 | 3 | 1 | 8.88e-16 | 1.87e-14 | 1.51e-14 | 1.51e-14 | 0.0000 | sim | 0.6248 | 8.9921 | sim | sim |
| shift_scheduling | 6 | 3 | 2 | 8.88e-16 | 2.13e-14 | 4.62e-14 | 4.62e-14 | 0.0000 | sim | 0.4111 | 10.3765 | sim | sim |
| shift_scheduling | 6 | 3 | 3 | 5.55e-16 | 2.44e-14 | 2.13e-14 | 2.13e-14 | 0.0000 | sim | 0.2140 | 9.9817 | sim | sim |
| shift_scheduling | 6 | 3 | 4 | 8.88e-16 | 1.42e-14 | 1.78e-14 | 1.95e-14 | 0.0000 | sim | 0.0334 | 10.6488 | sim | sim |
| shift_scheduling | 8 | 4 | 0 | 1.78e-15 | 1.71e-13 | 1.42e-13 | 1.42e-13 | 0.0000 | sim | 0.2219 | 15.0112 | sim | sim |
| shift_scheduling | 8 | 4 | 1 | 1.33e-15 | 1.14e-13 | 9.95e-14 | 1.14e-13 | 8.88e-16 | sim | 0.4286 | 12.9270 | sim | sim |
| shift_scheduling | 8 | 4 | 2 | 1.33e-15 | 1.14e-13 | 1.71e-13 | 1.71e-13 | 8.88e-16 | sim | 0.3382 | 16.7840 | sim | sim |
| shift_scheduling | 8 | 4 | 3 | 1.78e-15 | 4.62e-14 | 9.59e-14 | 9.41e-14 | 4.44e-16 | sim | 0.1187 | 14.9205 | sim | sim |
| shift_scheduling | 8 | 4 | 4 | 1.78e-15 | 1.99e-13 | 8.88e-14 | 1.14e-13 | 0.0000 | sim | 0.3760 | 15.1365 | sim | sim |
