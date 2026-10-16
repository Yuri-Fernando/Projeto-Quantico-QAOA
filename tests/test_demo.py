"""Demonstrador de 5 passos: HTML gerado offline, marcação REAL/SIMULADO e guarda de QPU."""
import pytest

from experiments.demo import main


@pytest.mark.parametrize("backend", ["ideal", "noisy", "fake"])
def test_demo_writes_report_marked_as_simulation(tmp_path, backend):
    out = tmp_path / "demo.html"
    main(["--n", "4", "--p", "1", "--maxiter", "30", "--shots", "256", "--backend", backend,
          "--fake-backend", "generic_line_4", "--out", str(out)])
    page = out.read_text(encoding="utf-8")
    assert "NÃO — simulação clássica" in page
    assert "objective_id" in page and "data:image/png;base64" in page


def test_demo_refuses_qpu_without_opt_in(tmp_path):
    with pytest.raises(SystemExit, match="QPU não executada"):
        main(["--n", "4", "--backend", "qpu", "--out", str(tmp_path / "q.html")])
