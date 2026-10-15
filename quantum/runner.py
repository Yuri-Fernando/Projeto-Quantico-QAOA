"""Laço variacional QAOA instrumentado (auditoria P0.3/P0.4, Epic B).

O otimizador clássico roda em CPU sobre a simulação IDEAL exata (``quantum.simulator``). Com
``objective_mode="sampled"`` cada avaliação usa uma estimativa de ``eval_shots`` amostras (ruído de
amostragem finita, como num hardware sem ruído de porta). Depois da otimização:

1. probabilidades exatas da evolução ideal -> ``analyze_probabilities`` (``*_exact``);
2. ``shots`` amostras finitas dessas probabilidades -> ``analyze_counts``.

Executar o MESMO circuito otimizado em outro backend (Aer ruidoso, fake, GPU, QPU) é papel do
orquestrador (``hpc.orchestrator``), que reaproveita ``params_final`` — protocolo de transferência
descrito em ``docs/EXPERIMENT_PROTOCOL.md``.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from math import comb
from typing import Optional

import numpy as np
from scipy.optimize import minimize

from optimization.canonical_qubo import QUBO, CardinalityProblem, IsingHamiltonian
from optimization.classical_qubo import solve_enumeration

from .measurement import analyze_counts, analyze_probabilities
from .simulator import ExactQAOASimulator, sample_counts

OPTIMIZERS = ("cobyla", "spsa")
INIT_STRATEGIES = ("uniform_small", "linear_ramp", "random")


@dataclass
class QAOAConfig:
    p: int = 1
    mixer: str = "x"  # "x" (+ penalidade) | "xy_ring" (+ Dicke, sem penalidade)
    penalty_factor: float = 1.0  # multiplica a penalidade segura (só mixer "x")
    optimizer: str = "cobyla"
    maxiter: int = 200
    init_strategy: str = "linear_ramp"
    seed: int = 0
    shots: int = 1024
    objective_mode: str = "exact"  # "exact" | "sampled"
    eval_shots: Optional[int] = None  # None -> usa `shots` (shots por avaliação no modo "sampled")

    def __post_init__(self):
        if self.p < 1:
            raise ValueError("p >= 1")
        if self.optimizer not in OPTIMIZERS:
            raise ValueError(f"optimizer em {OPTIMIZERS}")
        if self.init_strategy not in INIT_STRATEGIES:
            raise ValueError(f"init_strategy em {INIT_STRATEGIES}")
        if self.objective_mode not in ("exact", "sampled"):
            raise ValueError("objective_mode em ('exact', 'sampled')")
        if self.mixer not in ("x", "xy_ring"):
            raise ValueError("mixer em ('x', 'xy_ring')")

    @property
    def init(self) -> str:
        return "dicke" if self.mixer == "xy_ring" else "plus"


@dataclass
class QAOARun:
    record: dict
    problem: CardinalityProblem
    qubo: QUBO
    ising: IsingHamiltonian
    params_final: np.ndarray
    probabilities: np.ndarray
    f_star: float
    extras: dict = field(default_factory=dict)


def initial_point(strategy: str, p: int, rng: np.random.Generator) -> np.ndarray:
    if strategy == "uniform_small":  # política da v0.2.0
        return rng.uniform(0.0, 0.1, size=2 * p)
    if strategy == "linear_ramp":  # anelamento discretizado (determinístico)
        t = (np.arange(p) + 0.5) / p
        return np.concatenate([0.75 * t, 0.75 * (1.0 - t)])
    return np.concatenate([rng.uniform(0.0, np.pi, size=p), rng.uniform(0.0, np.pi / 2, size=p)])


def spsa_minimize(fun, x0: np.ndarray, maxiter: int, rng: np.random.Generator,
                  a: float = 0.3, c: float = 0.1, alpha: float = 0.602, gamma: float = 0.101):
    """SPSA (Spall) com ganhos padrão; 2 avaliações por iteração; devolve o melhor ponto visto."""
    x = np.asarray(x0, dtype=float).copy()
    A = 0.1 * maxiter
    best_x, best_f = x.copy(), fun(x)
    evals = 1
    for it in range(maxiter):
        ak = a / (it + 1 + A) ** alpha
        ck = c / (it + 1) ** gamma
        delta = rng.choice([-1.0, 1.0], size=x.size)
        fp, fm = fun(x + ck * delta), fun(x - ck * delta)
        evals += 2
        x = x - ak * (fp - fm) / (2 * ck) * delta
        for cand, val in ((x + ck * delta, fp), (x - ck * delta, fm)):
            if val < best_f:
                best_f, best_x = val, cand.copy()
    f_last = fun(x)
    evals += 1
    if f_last < best_f:
        best_f, best_x = f_last, x.copy()
    return best_x, best_f, evals


def run_qaoa(problem: CardinalityProblem, cfg: QAOAConfig, f_star: Optional[float] = None,
             enumeration: Optional[dict] = None) -> QAOARun:
    timings: dict[str, float] = {}
    t0 = time.perf_counter()
    rho = problem.safe_penalty() * cfg.penalty_factor if cfg.mixer == "x" else 0.0
    qubo = problem.penalized_qubo(rho)
    ising = qubo.to_ising()
    energies = qubo.energies()
    if enumeration is None and f_star is None:
        enumeration = solve_enumeration(problem)
    if f_star is None:
        f_star = enumeration["objective"]
    timings["time_preprocess"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    sim = ExactQAOASimulator(ising, cfg.p, mixer=cfg.mixer, init=cfg.init, k=problem.k)
    timings["time_build"] = time.perf_counter() - t0

    e_min, e_max = float(energies.min()), float(energies.max())
    e_span = (e_max - e_min) or 1.0
    rng_eval = np.random.default_rng([cfg.seed, 1])
    eval_shots = cfg.eval_shots or cfg.shots
    n_evals = 0

    def objective(params):
        nonlocal n_evals
        n_evals += 1
        probs = sim.probabilities(params)
        if cfg.objective_mode == "exact":
            value = float(probs @ energies)
        else:
            draws = rng_eval.multinomial(eval_shots, probs)
            value = float(draws @ energies / eval_shots)
        return (value - e_min) / e_span

    rng_init = np.random.default_rng([cfg.seed, 0])
    x0 = initial_point(cfg.init_strategy, cfg.p, rng_init)
    t0 = time.perf_counter()
    if cfg.optimizer == "cobyla":
        res = minimize(objective, x0, method="COBYLA", options={"maxiter": cfg.maxiter, "rhobeg": 0.3})
        params, opt_value, opt_msg = np.asarray(res.x), float(res.fun), str(res.message)
    else:
        params, opt_value, _ = spsa_minimize(objective, x0, cfg.maxiter, np.random.default_rng([cfg.seed, 2]))
        opt_msg = "spsa_completed"
    timings["time_classical_opt"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    probs = sim.probabilities(params)
    exact = analyze_probabilities(problem, probs, f_star, energies)
    timings["time_exact_eval"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    counts = sample_counts(probs, cfg.shots, np.random.default_rng([cfg.seed, 3]))
    timings["time_sampling"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    sampled = analyze_counts(problem, counts, f_star, qubo_energy=qubo.evaluate)
    timings["time_postprocess"] = time.perf_counter() - t0

    n_optimal = enumeration["n_optimal"] if enumeration else None
    record = {
        "objective_id": problem.objective_id,
        "instance_hash": problem.instance_hash,
        "domain": problem.domain,
        "n": problem.n,
        "k": problem.k,
        "algorithm": f"qaoa_{cfg.mixer}",
        "config": asdict(cfg),
        "penalty_rho": rho,
        "penalty_safe": problem.safe_penalty(),
        "qubo_offset": qubo.offset,
        "hamiltonian_scale": sim.scale,
        "n_zz_terms": len(ising.edges()),
        "params_initial": x0.tolist(),
        "params_final": params.tolist(),
        "optimizer_message": opt_msg,
        "optimizer_value_normalized": opt_value,
        "circuit_evaluations": n_evals,
        "shots_total": cfg.shots + (n_evals * eval_shots if cfg.objective_mode == "sampled" else 0),
        "f_star": f_star,
        "p_optimum_uniform_feasible": (n_optimal / comb(problem.n, problem.k)) if n_optimal else None,
        "p_optimum_uniform_all": (n_optimal / 2**problem.n) if n_optimal else None,
        "simulation": "ideal_exact_statevector+multinomial_sampling",
        "is_real_hardware": False,
        "timings": timings,
        **exact,
        **sampled,
    }
    record["timings"]["time_total"] = sum(timings.values())
    return QAOARun(record=record, problem=problem, qubo=qubo, ising=ising, params_final=params,
                   probabilities=probs, f_star=f_star, extras={"counts": counts})
