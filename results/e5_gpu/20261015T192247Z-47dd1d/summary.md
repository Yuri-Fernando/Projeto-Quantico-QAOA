# e5_gpu — resumo gerado de `records.jsonl`

- run_id: `20261015T192247Z-47dd1d` · kind: `devices` · track: `hpc`
- commit: `fc936b306ae185aba003a6ff2933b24877c54ceb` (working tree suja: False)
- config_hash: `6509ab1b2faae5c9` · registros: 9 · tempo de parede: 20.4s · modo quick: False
- Python 3.10.8 · qiskit 1.4.6 · qiskit-aer 0.17.2 · GPU: host_has_nvidia_gpu_but_qiskit_aer_build_is_cpu_only
- Toda execução quântica aqui é SIMULAÇÃO em CPU (`is_real_hardware=false`), salvo indicação explícita.
- GPU NVIDIA no host: `[{'name': 'NVIDIA GeForce RTX 3060 Ti', 'memory_total': '8192 MiB', 'driver': '617.42'}]`
- `AerSimulator().available_devices()`: `['CPU']`
- Status: **host_has_nvidia_gpu_but_qiskit_aer_build_is_cpu_only**

| n | requested_device | status | device_used | time_execution_median_s | statevector_bytes | reason |
|---|---|---|---|---|---|---|
| 10 | CPU | completed | CPU | 0.0133 | 16384 | — |
| 10 | GPU | not_executed | — | — | — | GPU não disponível no qiskit-aer instalado (available_devices=('CPU',)) |
| 14 | CPU | completed | CPU | 0.0220 | 262144 | — |
| 14 | GPU | not_executed | — | — | — | GPU não disponível no qiskit-aer instalado (available_devices=('CPU',)) |
| 18 | CPU | completed | CPU | 0.1155 | 4194304 | — |
| 18 | GPU | not_executed | — | — | — | GPU não disponível no qiskit-aer instalado (available_devices=('CPU',)) |
| 22 | CPU | completed | CPU | 0.9255 | 67108864 | — |
| 22 | GPU | not_executed | — | — | — | GPU não disponível no qiskit-aer instalado (available_devices=('CPU',)) |
