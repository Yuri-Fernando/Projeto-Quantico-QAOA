"""Transpilation hardware-aware: circuito lógico × físico (auditoria P1.1, experimento E2).

``swap_count`` é medido ANTES da tradução para a base nativa: o mesmo pass manager (mesma seed) é
executado só até o estágio de ``routing``, onde os ``SwapGate`` inseridos ainda são visíveis. Depois
da tradução cada SWAP vira 3 CX e deixa de ser identificável — por isso ele não é inferido do
circuito final. ``target_check`` confirma que toda instrução do circuito ISA é suportada pelo
``Target`` do backend nos qubits físicos usados (T07).
"""
from __future__ import annotations

import time

from qiskit import QuantumCircuit
from qiskit.transpiler import StagedPassManager
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

_NON_GATES = {"measure", "barrier", "reset", "delay"}


def _two_qubit_count(circuit: QuantumCircuit) -> int:
    return sum(1 for ins in circuit.data if ins.operation.num_qubits == 2 and ins.operation.name not in _NON_GATES)


def logical_metrics(circuit: QuantumCircuit) -> dict:
    """Métricas do circuito lógico (portas abstratas: rz, rzz, rx, rxx, ryy, cry, ccry...)."""
    ops = dict(circuit.count_ops())
    return {
        "num_qubits_logical": circuit.num_qubits,
        "depth_logical": circuit.depth(),
        "size_logical": circuit.size(),
        "count_ops_logical": {k: int(v) for k, v in ops.items()},
        "two_qubit_gates_logical": _two_qubit_count(circuit),
        "multi_qubit_gates_logical": sum(1 for ins in circuit.data if ins.operation.num_qubits >= 3),
    }


def _active_qubits(circuit: QuantumCircuit) -> list:
    used = set()
    for ins in circuit.data:
        if ins.operation.name in ("barrier", "delay"):
            continue
        for q in ins.qubits:
            used.add(circuit.find_bit(q).index)
    return sorted(used)


def target_check(circuit: QuantumCircuit, backend) -> tuple[bool, list]:
    target = backend.target
    bad = []
    for ins in circuit.data:
        name = ins.operation.name
        if name == "barrier":
            continue
        qargs = tuple(circuit.find_bit(q).index for q in ins.qubits)
        if not target.instruction_supported(name, qargs):
            bad.append((name, qargs))
    return (not bad), bad[:10]


def transpile_with_metrics(circuit: QuantumCircuit, backend, optimization_level: int = 1,
                           seed_transpiler: int = 0, layout_method: str | None = None,
                           routing_method: str | None = None) -> tuple[QuantumCircuit, dict]:
    """Transpila para o ``Target`` do backend e devolve ``(circuito_isa, métricas)``."""
    pm = generate_preset_pass_manager(optimization_level=optimization_level, backend=backend,
                                      seed_transpiler=seed_transpiler, layout_method=layout_method,
                                      routing_method=routing_method)
    t0 = time.perf_counter()
    isa = pm.run(circuit)
    t_transpile = time.perf_counter() - t0

    stages = {name: getattr(pm, name) for name in ("init", "layout", "routing") if getattr(pm, name) is not None}
    routed = StagedPassManager(stages=list(stages), **stages).run(circuit) if stages else circuit
    swaps = int(routed.count_ops().get("swap", 0))

    ok, bad = target_check(isa, backend)
    layout = isa.layout.initial_index_layout(filter_ancillas=True) if isa.layout is not None else None
    final = isa.layout.final_index_layout(filter_ancillas=True) if isa.layout is not None else None
    coupling = backend.coupling_map
    metrics = {
        "backend_name": backend.name,
        "num_qubits_device": backend.num_qubits,
        "coupling_edges": len(coupling.get_edges()) if coupling is not None else None,
        "basis_gates": sorted(set(backend.operation_names) - _NON_GATES),
        "optimization_level": optimization_level,
        "seed_transpiler": seed_transpiler,
        "layout_method": layout_method or "default",
        "routing_method": routing_method or "default",
        "transpile_time_s": t_transpile,
        "depth_physical": isa.depth(),
        "depth_two_qubit_physical": isa.depth(lambda ins: ins.operation.num_qubits == 2),
        "size_physical": isa.size(),
        "count_ops_physical": {k: int(v) for k, v in isa.count_ops().items()},
        "two_qubit_gates_physical": _two_qubit_count(isa),
        "swap_count": swaps,
        "num_qubits_physical_active": len(_active_qubits(isa)),
        "initial_layout": layout,
        "final_layout": final,
        "target_supported": ok,
        "target_violations": bad,
    }
    metrics.update(logical_metrics(circuit))
    return isa, metrics


def basis_only_transpile(circuit: QuantumCircuit, basis_gates=("rz", "sx", "x", "cx"),
                         optimization_level: int = 1, seed_transpiler: int = 0) -> QuantumCircuit:
    """Traduz para uma base nativa SEM restrição de conectividade (all-to-all) — regime de ruído sem topologia."""
    from qiskit import transpile

    return transpile(circuit, basis_gates=list(basis_gates), optimization_level=optimization_level,
                     seed_transpiler=seed_transpiler)
