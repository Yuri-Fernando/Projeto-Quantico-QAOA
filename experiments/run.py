"""Executor de experimentos por config YAML (tudo offline; QPU só com ``--allow-qpu``).

Tipos (``kind``):
  equivalence          E0  paridade f / QUBO / Ising / Pauli / MILP / enumeração
  algorithm_benchmark  E1, E4, E7  clássicos + QAOA no MESMO objetivo, várias seeds
  transpilation        E2  métricas lógicas x físicas por backend fake / nível / seed
  noise                E3  parâmetros otimizados no ideal, executados sob regimes de ruído
  devices              E5  CPU x GPU (GPU somente se o Aer a expuser)
  qpu                  E6  IBM QPU (opt-in); sem opt-in/credenciais registra o bloqueio

Uso:
  python -m experiments.run --config experiments/configs/e1_ideal_qaoa.yaml [--quick] [--allow-qpu]
"""
from __future__ import annotations

import argparse
import itertools
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import yaml

from hpc.devices import aer_available_devices, detect_devices
from hpc.orchestrator import make_backend, run_pipeline
from optimization.canonical_qubo import CardinalityProblem, basis_matrix, critical_penalty, index_to_x
from optimization.classical_qubo import solve_enumeration, solve_milp_linearized
from optimization.heuristics import random_feasible_sampling, simulated_annealing
from optimization.instance import generate_portfolio_instance
from optimization.scheduling import generate_shift_scheduling_instance
from quantum.ansatz import bind, build_qaoa_circuit
from quantum.backends import AerBackend, GPUUnavailable, QPUNotAllowed, QPUUnavailable
from quantum.measurement import analyze_counts
from quantum.noise import get_fake_backend
from quantum.runner import QAOAConfig, initial_point, run_qaoa
from quantum.transpilation import transpile_with_metrics

from .schemas import ROOT, RunWriter, build_manifest

KINDS = ("equivalence", "algorithm_benchmark", "transpilation", "noise", "devices", "qpu")


# --------------------------------------------------------------------------- utilitários
def load_config(path: Path, quick: bool = False) -> dict:
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if quick and "quick" in cfg:
        cfg = _deep_merge(cfg, cfg["quick"])
        cfg["quick_mode"] = True
    cfg.pop("quick", None)
    if cfg.get("kind") not in KINDS:
        raise ValueError(f"kind deve ser um de {KINDS}")
    return cfg


def _deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        out[k] = _deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def _k_for(n: int, spec) -> int:
    return n // 2 if spec in (None, "half") else int(spec)


def make_problem(domain: str, n: int, seed: int, k_spec=None) -> tuple[CardinalityProblem, object]:
    k = _k_for(n, k_spec)
    if domain == "portfolio":
        inst = generate_portfolio_instance(n, k=k, seed=seed)
    elif domain == "shift_scheduling":
        inst = generate_shift_scheduling_instance(n, k=k, seed=seed)
    else:
        raise ValueError(f"domínio desconhecido: {domain}")
    return inst.to_problem(), inst


def instances(cfg: dict) -> Iterator[tuple[str, int, int, CardinalityProblem, object]]:
    ic = cfg["instances"]
    for domain in ic.get("domains", ["portfolio"]):
        for n in ic["sizes"]:
            for seed in ic.get("seeds", [0]):
                problem, inst = make_problem(domain, n, seed, ic.get("k", "half"))
                yield domain, n, seed, problem, inst


def grid(spec: dict) -> Iterator[dict]:
    keys = list(spec)
    for values in itertools.product(*(v if isinstance(v, list) else [v] for v in spec.values())):
        yield dict(zip(keys, values))


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _base(problem: CardinalityProblem, inst_seed: int) -> dict:
    return {"domain": problem.domain, "objective_id": problem.objective_id, "instance_hash": problem.instance_hash,
            "n": problem.n, "k": problem.k, "instance_seed": inst_seed}


# --------------------------------------------------------------------------- E0
def run_equivalence(cfg: dict, w: RunWriter, **_) -> None:
    for _domain, n, seed, problem, inst in instances(cfg):
        X = basis_matrix(n).astype(float)
        f = problem.evaluate_many(X)
        f_orig = np.array([_original_objective(inst, x) for x in X])
        rho = problem.safe_penalty()
        qubo = problem.penalized_qubo(rho)
        e_qubo = qubo.energies()
        ising = qubo.to_ising()
        diffs = {
            "max_abs_f_vs_original": float(np.abs(f - f_orig).max()),
            "max_abs_qubo_vs_f_plus_penalty": float(np.abs(e_qubo - (f + rho * (X.sum(1) - problem.k) ** 2)).max()),
            "max_abs_ising_vs_qubo": float(np.abs(ising.energies() - e_qubo).max()),
        }
        if n <= 8:
            diag = np.real(np.diag(ising.to_sparse_pauli_op().to_matrix()))
            diffs["max_abs_pauli_vs_qubo"] = float(np.abs(diag - e_qubo).max())
        exact = solve_enumeration(problem)
        milp = solve_milp_linearized(problem)
        lp = solve_milp_linearized(problem, relax=True)
        ground = index_to_x(int(np.argmin(e_qubo)), n)
        rec = {
            **_base(problem, seed), **diffs,
            "f_star_enumeration": exact["objective"], "f_star_milp": milp["objective"],
            "abs_diff_milp_vs_enumeration": abs(milp["objective"] - exact["objective"]),
            "milp_status": milp["status"], "lp_relaxation_bound": lp["objective"],
            "lp_le_milp": lp["objective"] <= milp["objective"] + 1e-7,
            "n_optimal": exact["n_optimal"],
            "safe_penalty": rho, "critical_penalty": critical_penalty(problem),
            "qubo_ground_state_feasible": problem.is_feasible(ground),
            "qubo_ground_state_is_optimal": abs(problem.evaluate(ground) - exact["objective"]) < 1e-9,
        }
        rec["pass"] = bool(max(diffs.values()) < 1e-9 and rec["abs_diff_milp_vs_enumeration"] < 1e-7
                           and rec["lp_le_milp"] and rec["qubo_ground_state_is_optimal"])
        w.write(rec)


def _original_objective(inst, x) -> float:
    if hasattr(inst, "quadratic_objective"):
        return inst.quadratic_objective(x)
    S = inst.shared_resources
    return float(-inst.priority @ x + inst.alpha * sum(S[i, j] * x[i] * x[j]
                                                      for i in range(inst.n) for j in range(i + 1, inst.n)))


# --------------------------------------------------------------------------- E1/E4/E7
def run_algorithm_benchmark(cfg: dict, w: RunWriter, **_) -> None:
    classical = cfg.get("classical", {})
    qcfg = cfg.get("qaoa", {})
    backend_spec = cfg.get("backend")
    backend = make_backend(backend_spec) if backend_spec else None
    for _domain, n, inst_seed, problem, _inst in instances(cfg):
        t0 = time.perf_counter()
        exact = solve_enumeration(problem)
        exact["time_s"] = time.perf_counter() - t0
        base = _base(problem, inst_seed)
        f_star = exact["objective"]
        w.write({**base, "algorithm": "enumeration", "objective": f_star, "gap_abs": 0.0, "time_s": exact["time_s"],
                 "n_optimal": exact["n_optimal"], "n_feasible": exact["n_feasible"], "certified": True})
        if classical.get("milp", True) and n <= classical.get("milp_max_n", 64):
            milp = solve_milp_linearized(problem, time_limit=classical.get("time_limit", 60))
            w.write({**base, "algorithm": "milp_linearized", "objective": milp["objective"],
                     "gap_abs": milp["objective_recomputed"] - f_star, "time_s": milp["time_s"],
                     "time_build_s": milp["time_build_s"], "time_solve_s": milp["time_solve_s"],
                     "status": milp["status"], "certified": milp["certified"], "n_aux_vars": milp["n_aux_vars"]})
            lp = solve_milp_linearized(problem, relax=True)
            w.write({**base, "algorithm": "lp_relaxation_mccormick", "objective": lp["objective"],
                     "lower_bound_gap": f_star - lp["objective"], "time_s": lp["time_s"], "status": lp["status"]})
        for seed in classical.get("seeds", [0]):
            sa = simulated_annealing(problem, seed=seed, n_steps=classical.get("sa_steps", 2000))
            w.write({**base, "algorithm": "simulated_annealing", "seed": seed, "objective": sa["objective"],
                     "gap_abs": sa["objective"] - f_star, "is_optimal": sa["objective"] <= f_star + 1e-9,
                     "evaluations": sa["evaluations"], "time_s": sa["time_s"]})
            n_samples = classical.get("random_samples", 1024)
            rnd = random_feasible_sampling(problem, n_samples=n_samples, seed=seed, f_star=f_star)
            w.write({**base, "algorithm": "random_feasible_sampling", "seed": seed, "objective": rnd["objective"],
                     "gap_abs": rnd["objective"] - f_star, "is_optimal": rnd["objective"] <= f_star + 1e-9,
                     "p_optimum": rnd["p_optimum"], "evaluations": n_samples, "time_s": rnd["time_s"]})
        if not qcfg:
            continue
        for params in grid(qcfg.get("grid", {})):
            if n > qcfg.get("max_n", 64) or (params.get("p", 1) > qcfg.get("max_p_for_n", {}).get(n, 99)):
                continue
            for seed in qcfg.get("seeds", [0]):
                cfg_q = QAOAConfig(**{"maxiter": qcfg.get("maxiter", 200),
                                      "objective_mode": qcfg.get("objective_mode", "exact"), **params, "seed": seed})
                out = run_pipeline(problem, cfg_q, backend=backend, enumeration=exact,
                                   profile_memory=qcfg.get("profile_memory", True))
                rec = out["record"]
                rec.pop("config", None)
                w.write({**base, **params, "seed": seed, **rec}, counts=out["counts"])
        _log(f"[{cfg['experiment']}] {problem.domain} n={n} seed={inst_seed} ok ({w.n_records} registros)")


# --------------------------------------------------------------------------- E2
def run_transpilation(cfg: dict, w: RunWriter, **_) -> None:
    tc = cfg["transpilation"]
    for _domain, n, inst_seed, problem, _inst in instances(cfg):
        for mixer in tc.get("mixers", ["x"]):
            ising = problem.penalized_qubo(None if mixer == "x" else 0.0).to_ising()
            init = "plus" if mixer == "x" else "dicke"
            for p in tc.get("p", [1]):
                params = initial_point("linear_ramp", p, np.random.default_rng(0))
                circuit = bind(build_qaoa_circuit(ising, p, mixer, init, problem.k, measure=True), params)
                for bname_t in tc["backends"]:
                    bname = bname_t.format(n=n)
                    backend = _cached_fake(bname)
                    if backend.num_qubits < n:
                        continue
                    for level in tc.get("optimization_levels", [1]):
                        for tseed in tc.get("seeds", [0]):
                            _, m = transpile_with_metrics(circuit, backend, level, tseed)
                            w.write({**_base(problem, inst_seed), "mixer": mixer, "p": p,
                                     "backend_family": bname_t.replace("{n}", "N"), **m})
        _log(f"[{cfg['experiment']}] {problem.domain} n={n} ok ({w.n_records} registros)")


_FAKE_CACHE: dict[str, object] = {}


def _cached_fake(name: str):
    if name not in _FAKE_CACHE:
        _FAKE_CACHE[name] = get_fake_backend(name)
    return _FAKE_CACHE[name]


# --------------------------------------------------------------------------- E3
def run_noise(cfg: dict, w: RunWriter, **_) -> None:
    nc = cfg["noise"]
    regimes: list[dict] = nc["regimes"]
    backends: dict[str, AerBackend] = {}
    for _domain, n, inst_seed, problem, _inst in instances(cfg):
        exact = solve_enumeration(problem)
        for params in grid(nc.get("grid", {})):
            for seed in nc.get("seeds", [0]):
                cfg_q = QAOAConfig(**{"maxiter": nc.get("maxiter", 200), "shots": nc.get("shots", 4096),
                                      **params, "seed": seed})
                run = run_qaoa(problem, cfg_q, enumeration=exact)
                circuit = bind(build_qaoa_circuit(run.ising, cfg_q.p, cfg_q.mixer, cfg_q.init, problem.k,
                                                  measure=True), run.params_final)
                ref = {k: run.record[k] for k in ("p_optimum_exact", "p_feasible_exact", "expected_energy_exact")}
                for reg in regimes:
                    label = reg["label"]
                    if label not in backends:
                        backends[label] = AerBackend(regime=reg.get("regime", "ideal"),
                                                     fake_backend=reg.get("fake_backend"),
                                                     noise_params=reg.get("noise_params"),
                                                     optimization_level=reg.get("optimization_level", 1))
                    backend = backends[label]
                    if backend.fake is not None and backend.fake.num_qubits < n:
                        continue
                    res = backend.run(circuit, shots=cfg_q.shots, seed=seed)
                    metrics = analyze_counts(problem, res.counts, run.f_star, run.qubo.evaluate)
                    exec_info = res.to_dict(include_counts=False)
                    w.write({**_base(problem, inst_seed), **params, "seed": seed, "regime_label": label,
                             "noise_params": reg.get("noise_params"), "ideal_reference": ref,
                             "execution": exec_info, **metrics}, counts=res.counts)
        _log(f"[{cfg['experiment']}] {problem.domain} n={n} ok ({w.n_records} registros)")


# --------------------------------------------------------------------------- E5
def run_devices(cfg: dict, w: RunWriter, **_) -> None:
    dc = cfg["devices"]
    info = detect_devices()
    w.write({"record_type": "device_detection", **info})
    for n in dc["sizes"]:
        problem, _ = make_problem("portfolio", n, 0)
        ising = problem.penalized_qubo().to_ising()
        circuit = bind(build_qaoa_circuit(ising, dc.get("p", 1), measure=True),
                       initial_point("linear_ramp", dc.get("p", 1), np.random.default_rng(0)))
        for device in dc.get("targets", ["CPU", "GPU"]):
            base = {"record_type": "execution", "n": n, "requested_device": device, "shots": dc.get("shots", 1024)}
            try:
                backend = AerBackend(device=device, allow_cpu_fallback=False, method=dc.get("method", "statevector"))
            except GPUUnavailable as exc:
                w.write({**base, "status": "not_executed", "reason": str(exc),
                         "aer_available_devices": list(aer_available_devices())})
                continue
            times = []
            for rep in range(dc.get("repeats", 3)):
                res = backend.run(circuit, shots=base["shots"], seed=rep)
                times.append(res.elapsed["time_quantum_execution"])
            w.write({**base, "status": "completed", "device_used": res.device, "is_real_hardware": False,
                     "time_execution_s": times, "time_execution_median_s": float(np.median(times)),
                     "aer_reported_s": res.elapsed.get("time_aer_reported"),
                     "statevector_bytes": 16 * 2**n, "warnings": res.warnings})
        _log(f"[{cfg['experiment']}] n={n} ok")


# --------------------------------------------------------------------------- E6
def run_qpu(cfg: dict, w: RunWriter, allow_qpu: bool = False, **_) -> None:
    qc = cfg["qpu"]
    problem, _ = make_problem("portfolio", qc.get("n", 4), qc.get("instance_seed", 0))
    base = {**_base(problem, qc.get("instance_seed", 0)), "backend_name": qc["backend_name"],
            "dry_run": qc.get("dry_run", True), "shots": qc.get("shots", 1000)}
    if not allow_qpu:
        w.write({**base, "status": "not_executed", "reason": "sem --allow-qpu (opt-in obrigatório)",
                 "is_real_hardware": False})
        return
    run = run_qaoa(problem, QAOAConfig(p=qc.get("p", 1), mixer=qc.get("mixer", "x"), seed=0, maxiter=100))
    circuit = bind(build_qaoa_circuit(run.ising, run.record["config"]["p"], run.record["config"]["mixer"],
                                      "dicke" if run.record["config"]["mixer"] == "xy_ring" else "plus",
                                      problem.k, measure=True), run.params_final)
    try:
        backend = make_backend({"type": "ibm_qpu", **qc}, allow_qpu=True)
        res = backend.run(circuit, shots=base["shots"], seed=0)
    except (QPUUnavailable, QPUNotAllowed) as exc:
        w.write({**base, "status": "BLOCKED_BY_CONFIGURATION" if isinstance(exc, QPUUnavailable) else "refused",
                 "reason": str(exc), "is_real_hardware": False})
        return
    metrics = analyze_counts(problem, res.counts, run.f_star, run.qubo.evaluate) if res.counts else None
    w.write({**base, "status": res.status, "execution": res.to_dict(include_counts=False), "metrics": metrics,
             "ideal_reference": {"p_optimum_exact": run.record["p_optimum_exact"]}}, counts=res.counts or None)


HANDLERS = {"equivalence": run_equivalence, "algorithm_benchmark": run_algorithm_benchmark,
            "transpilation": run_transpilation, "noise": run_noise, "devices": run_devices, "qpu": run_qpu}


def main(argv: list[str] | None = None) -> Path:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--quick", action="store_true", help="usa a seção 'quick' da config (CI/smoke)")
    ap.add_argument("--allow-qpu", action="store_true", help="autoriza submissão a QPU real (consome cota)")
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--no-analyze", action="store_true")
    args = ap.parse_args(argv)

    cfg = load_config(Path(args.config), quick=args.quick)
    manifest = build_manifest(cfg["experiment"], cfg["kind"], cfg.get("track", cfg["kind"]), cfg,
                              ["python -m experiments.run", *argv])
    manifest["allow_qpu"] = bool(args.allow_qpu)
    writer = RunWriter(Path(args.out), manifest)
    t0 = time.perf_counter()
    status = "completed"
    try:
        HANDLERS[cfg["kind"]](cfg, writer, allow_qpu=args.allow_qpu)
    except Exception as exc:
        status = f"failed: {type(exc).__name__}: {exc}"
        raise
    finally:
        run_dir = writer.close({"status": status, "wall_time_s": time.perf_counter() - t0})
        _log(f"execução salva em {run_dir}")
    if not args.no_analyze:
        from .analyze import analyze_run

        analyze_run(run_dir)
    return run_dir


if __name__ == "__main__":
    main()
