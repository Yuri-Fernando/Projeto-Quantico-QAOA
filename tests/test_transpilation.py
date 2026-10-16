"""T07/T08 — circuito ISA aceito pelo Target do backend fake; métricas lógicas/físicas preenchidas."""
import numpy as np
import pytest

from optimization.instance import generate_portfolio_instance
from quantum.ansatz import bind, build_qaoa_circuit
from quantum.noise import get_fake_backend
from quantum.transpilation import transpile_with_metrics


def _circuit(n=4, mixer="x", p=1):
    problem = generate_portfolio_instance(n, seed=0).to_problem()
    ising = problem.penalized_qubo(None if mixer == "x" else 0.0).to_ising()
    init = "plus" if mixer == "x" else "dicke"
    qc = build_qaoa_circuit(ising, p, mixer=mixer, init=init, k=problem.k, measure=True)
    return bind(qc, np.linspace(0.1, 0.8, 2 * p))


@pytest.mark.parametrize("backend_name", ["generic_line_4", "generic_heavyhex_d3", "fake27_snapshot"])
@pytest.mark.parametrize("mixer", ["x", "xy_ring"])
def test_isa_circuit_is_supported_by_target_and_metrics_filled(backend_name, mixer):
    backend = get_fake_backend(backend_name)
    isa, m = transpile_with_metrics(_circuit(mixer=mixer), backend, optimization_level=1, seed_transpiler=3)
    assert m["target_supported"], m["target_violations"]
    for key in ("depth_logical", "depth_physical", "two_qubit_gates_logical", "two_qubit_gates_physical",
                "swap_count", "transpile_time_s", "num_qubits_physical_active", "initial_layout"):
        assert m[key] is not None
    assert m["num_qubits_logical"] == 4
    assert len(m["initial_layout"]) == 4
    assert m["two_qubit_gates_physical"] >= 1
    assert set(isa.count_ops()) - {"measure", "barrier"} <= set(backend.operation_names)


def test_dense_problem_needs_swaps_on_line_but_not_on_all_to_all():
    circuit = _circuit(n=5)
    _, line = transpile_with_metrics(circuit, get_fake_backend("generic_line_5"), seed_transpiler=1)
    _, full = transpile_with_metrics(circuit, get_fake_backend("generic_all_to_all_5"), seed_transpiler=1)
    assert line["two_qubit_gates_logical"] == 10  # C(5,2) termos ZZ: grafo completo
    assert line["swap_count"] > 0
    assert full["swap_count"] == 0
    assert line["two_qubit_gates_physical"] > full["two_qubit_gates_physical"]


def test_transpilation_is_reproducible_with_same_seed():
    backend = get_fake_backend("generic_heavyhex_d3")
    _, a = transpile_with_metrics(_circuit(n=6), backend, optimization_level=2, seed_transpiler=11)
    _, b = transpile_with_metrics(_circuit(n=6), backend, optimization_level=2, seed_transpiler=11)
    for key in ("depth_physical", "two_qubit_gates_physical", "swap_count", "initial_layout"):
        assert a[key] == b[key]


def test_layout_is_recovered_when_qiskit_initial_index_layout_fails():
    """Regressão: Qiskit 1.4.6 levanta IndexError em initial_index_layout(filter_ancillas=True) neste caso."""
    from optimization.instance import generate_portfolio_instance as gen
    from quantum.runner import initial_point

    problem = gen(8, seed=0).to_problem()
    qc = bind(build_qaoa_circuit(problem.penalized_qubo().to_ising(), 2, measure=True),
              initial_point("linear_ramp", 2, None))
    _, m = transpile_with_metrics(qc, get_fake_backend("generic_heavyhex_d3"), optimization_level=1,
                                  seed_transpiler=0)
    assert m["target_supported"]
    assert len(m["initial_layout"]) == 8 and None not in m["initial_layout"]
    assert len(set(m["initial_layout"])) == 8
