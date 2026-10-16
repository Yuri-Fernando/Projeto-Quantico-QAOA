# Limitações de hardware e de simulação

Estado em 2026-10-15, medido nesta máquina (manifests em `results/`).

## Tudo aqui é simulação clássica em CPU

Nenhum resultado deste repositório foi obtido em QPU ou GPU. Todo registro carrega
`is_real_hardware=false` e `device="CPU"`.

## GPU — `host_has_nvidia_gpu_but_qiskit_aer_build_is_cpu_only`

- Host: NVIDIA GeForce RTX 3060 Ti, 8 GiB (`nvidia-smi`, driver 617.42).
- `qiskit-aer 0.17.2` instalado: `AerSimulator().available_devices() == ('CPU',)`.
- Os wheels do `qiskit-aer` publicados no PyPI para Windows são CPU; o pacote com CUDA
  (`qiskit-aer-gpu`) é distribuído para Linux. Instalar/compilar isso é decisão do proprietário
  (dependência de hardware, CUDA toolkit) e **não foi feito**.
- Consequência: E5 registra `not_executed` para GPU e mede apenas CPU. O teste de paridade CPU×GPU
  (`test_cpu_gpu_distributions_match`) dá *skip* com o motivo. Para executar: rodar E5 num host Linux
  com `qiskit-aer-gpu` e CUDA compatível; o adaptador usa GPU sozinho quando `available_devices()` a lista.

## QPU — `BLOCKED_BY_CONFIGURATION`

- `qiskit-ibm-runtime` não está instalado; nenhuma credencial IBM existe no ambiente.
- O adaptador `IBMQPUBackend` está implementado e testado **apenas com serviço/sampler simulados**
  (completo, timeout, falha, orçamento, dry-run). O caminho real nunca foi exercitado.
- A API do Runtime muda entre versões (primitives server-side × client-side, nomes de canal); conferir a
  documentação da versão instalada antes do primeiro job.
- Para executar E6: instalar `qiskit-ibm-runtime`, exportar `QISKIT_IBM_TOKEN` (e `QISKIT_IBM_INSTANCE`
  se necessário), ajustar `backend_name` e o orçamento em `e6_qpu.yaml`, rodar com `--allow-qpu`.
  `dry_run: true` (padrão) só transpila e valida o ISA; trocar para `false` consome cota.

## Backends fake

| Nome | Origem | Serve para | Não serve para |
|---|---|---|---|
| `generic_line_<n>` | `GenericBackendV2`, linha, erros sintéticos por seed | pior caso de conectividade | prever fidelidade |
| `generic_heavyhex_d3` | `GenericBackendV2`, heavy-hex distância 3 (19 qubits), erros sintéticos | topologia no estilo IBM | prever fidelidade |
| `fake27_snapshot` | `Fake27QPulseV1` (Qiskit 1.4), snapshot fixo de propriedades de 27 qubits | ruído com valores realistas de uma época | calibração atual; deprecated, removido no Qiskit 2.0 |
| `generic_all_to_all_<n>` | `GenericBackendV2`, conectividade completa | referência sem SWAPs | — |

Os snapshots realistas atuais ficam em `qiskit_ibm_runtime.fake_provider`, não instalado aqui.

## Limites de memória da simulação

Statevector `complex128`: `16 · 2^n` bytes (n=20: 16 MiB; n=30: 16 GiB; n=34: 256 GiB), antes de
overheads. Matriz densidade: `16 · 4^n` (n=14: 4 GiB). O E4 mede o pico real do processo; a
extrapolação acima é aritmética, não medição.

## Bugs/limitações de bibliotecas encontrados

- Qiskit 1.4.6: `Layout.initial_index_layout(filter_ancillas=True)` levanta `IndexError` em alguns
  layouts (reproduzido: heavy-hex 19q, nível 1, seed 0, n=8). Contornado em
  `quantum/transpilation.py` com teste de regressão.
- qiskit-aer 0.17.2 com Qiskit 1.4: milhares de `DeprecationWarning` internos
  (`Instruction.condition`); filtrados no `pyproject.toml`, não vêm deste código.
- `NoiseModel.to_dict()` inclui um `id` aleatório por erro; o hash do modelo remove esses ids.
