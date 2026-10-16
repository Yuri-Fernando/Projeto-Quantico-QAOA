# Execuções que não completaram (preservadas como evidência)

| Execução | Causa | Ação |
|---|---|---|
| `e2_hardware_aware/20261015T192353Z-e702d3` | `IndexError` do Qiskit 1.4.6 em `Layout.initial_index_layout(filter_ancillas=True)` (222 registros antes da falha) | contorno em `quantum/transpilation.py` (commit `2b5c85f`) e reexecução |
| `e3_noise/20261015T193528Z-b28969` | mesma causa, ao transpilar para o backend fake heavy-hex (726 registros) | idem |
| `e4_scalability/20261015T193920Z-ad740e` | processo terminou sem traceback e sem manifest no meio de n=18 (pico de RSS 287 MB); não reproduzido isoladamente | reexecutado com `-X faulthandler`; completou |

As contagens brutas (`raw_counts.jsonl.gz`) destas execuções não são versionadas.
