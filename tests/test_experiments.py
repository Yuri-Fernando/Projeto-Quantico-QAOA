"""T10/T13/T14/T17 — CLI offline (sem token IBM/GPU), manifesto, leitura/escrita e separação de trilhas."""
import gzip
import json
import sys
from pathlib import Path

import pytest

from benchmarks.compare_methods import render_markdown, run_benchmark
from experiments.run import main
from experiments.schemas import REQUIRED_MANIFEST_KEYS, REQUIRED_RECORD_KEYS, read_manifest, read_records

CONFIGS = sorted((Path(__file__).resolve().parent.parent / "experiments" / "configs").glob("*.yaml"))


@pytest.mark.parametrize("config", CONFIGS, ids=lambda p: p.stem)
def test_every_config_runs_offline_in_quick_mode(config, tmp_path, monkeypatch):
    monkeypatch.delenv("QISKIT_IBM_TOKEN", raising=False)
    run_dir = main(["--config", str(config), "--quick", "--out", str(tmp_path)])
    manifest = read_manifest(run_dir)
    for key in REQUIRED_MANIFEST_KEYS:
        assert key in manifest, key
    assert manifest["status"] == "completed" and manifest["allow_qpu"] is False
    records = list(read_records(run_dir))
    assert records and len(records) == manifest["n_records"]
    for rec in records:
        for key in REQUIRED_RECORD_KEYS:
            assert key in rec
        assert rec.get("is_real_hardware") in (None, False)  # T14: nada de hardware real
    assert (run_dir / "summary.md").read_text(encoding="utf-8").startswith("# ")
    with gzip.open(run_dir / "raw_counts.jsonl.gz", "rt", encoding="utf-8") as fh:
        for line in fh:
            assert sum(json.loads(line)["counts"].values()) > 0
    assert "qiskit_ibm_runtime" not in sys.modules


def test_qpu_experiment_without_opt_in_is_not_executed(tmp_path):
    run_dir = main(["--config", str(CONFIGS[0].parent / "e6_qpu.yaml"), "--out", str(tmp_path)])
    (rec,) = list(read_records(run_dir))
    assert rec["status"] == "not_executed" and rec["is_real_hardware"] is False


def test_algorithm_benchmark_methods_share_one_objective_per_instance(tmp_path):
    run_dir = main(["--config", str(CONFIGS[0].parent / "e1_ideal_qaoa.yaml"), "--quick", "--out", str(tmp_path)])
    by_instance = {}
    for rec in read_records(run_dir):
        by_instance.setdefault(rec["instance_hash"], set()).add(rec["objective_id"])
        assert rec["track"] == "algorithm_benchmark"
    assert by_instance and all(len(ids) == 1 for ids in by_instance.values())


def test_model_comparison_is_labelled_as_a_separate_track():
    report = run_benchmark()
    assert report["track"] == "model_comparison"
    kinds = {row["native_objective_kind"] for row in report["rows"]}
    assert kinds == {"mean_variance", "return_plus_shortfall"}
    md = render_markdown(report)
    assert "NÃO ranqueia algoritmos" in md and "statevector exato" not in md
