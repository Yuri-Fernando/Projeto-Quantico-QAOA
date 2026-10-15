"""Trilha MODEL_COMPARISON: LP vs MILP vs Estocástico vs Benders vs QAOA, na mesma instância.

ATENÇÃO — isto NÃO é um benchmark algoritmo-contra-algoritmo. LP/MILP/estocástico/Benders
minimizam retorno negativo + *shortfall* por cenários; o QAOA minimiza média-variância
(``-mu^T x + lam x^T Sigma x``). Mesmos dados, objetivos diferentes: a tabela compara
FORMULAÇÕES de risco. A comparação de algoritmos sobre o MESMO objetivo está em
``benchmarks/fair_qubo_benchmark.py`` (trilha ``algorithm_benchmark``).

Mede, para cada método, tempo de execução (``time.perf_counter``, uma execução), o valor
objetivo nativo do método, e reavalia a solução ``x`` encontrada nas DUAS métricas
definidas em ``optimization.instance``:

- ``quadratic_objective``: risco média-variância (nativo do QUBO/QAOA)
- ``expected_shortfall_metric``: risco de shortfall por cenário (nativo
  de LP/MILP/estocástico/Benders)

Os números deste relatório são MEDIDOS a cada execução — nenhum valor é inventado.

Uso:
    python -m benchmarks.compare_methods
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from optimization.benders import solve_benders
from optimization.instance import brute_force_optimum, build_instance
from optimization.lp import solve_lp_relaxation
from optimization.milp import solve_milp
from optimization.qaoa import solve_with_qaoa
from optimization.stochastic import solve_stochastic_extensive_form


def _x_to_tickers(instance, x):
    return [t for t, xi in zip(instance.tickers, x) if xi > 0.5]


def run_benchmark() -> dict:
    instance = build_instance()
    rows = []

    # --- Referência: busca exaustiva (ótimo real, métrica quadrática) ---
    t0 = time.perf_counter()
    bf_x, bf_val = brute_force_optimum(instance)
    t_bf = time.perf_counter() - t0
    rows.append(
        {
            "method": "Brute force (referência)",
            "time_s": t_bf,
            "native_objective": bf_val,
            "selected": _x_to_tickers(instance, bf_x),
            "quadratic_objective": instance.quadratic_objective(bf_x),
            "shortfall_metric": instance.expected_shortfall_metric(bf_x),
        }
    )

    # --- LP (relaxação contínua) ---
    t0 = time.perf_counter()
    lp = solve_lp_relaxation(instance)
    t_lp = time.perf_counter() - t0
    rows.append(
        {
            "method": "LP (relaxação linear)",
            "time_s": t_lp,
            "native_objective": lp["objective"],
            "selected": _x_to_tickers(instance, lp["x"]),
            "x_raw": lp["x"].tolist(),
            "quadratic_objective": instance.quadratic_objective(lp["x"]),
            "shortfall_metric": instance.expected_shortfall_metric(lp["x"]),
        }
    )

    # --- MILP ---
    t0 = time.perf_counter()
    milp = solve_milp(instance)
    t_milp = time.perf_counter() - t0
    rows.append(
        {
            "method": "MILP (Pyomo + HiGHS)",
            "time_s": t_milp,
            "native_objective": milp["objective"],
            "selected": _x_to_tickers(instance, milp["x"]),
            "quadratic_objective": instance.quadratic_objective(milp["x"]),
            "shortfall_metric": instance.expected_shortfall_metric(milp["x"]),
        }
    )

    # --- Estocástico (forma extensiva, 1ª etapa inteira) ---
    t0 = time.perf_counter()
    sto = solve_stochastic_extensive_form(instance, integer_first_stage=True)
    t_sto = time.perf_counter() - t0
    rows.append(
        {
            "method": "Estocástico 2 estágios (forma extensiva)",
            "time_s": t_sto,
            "native_objective": sto["objective"],
            "selected": _x_to_tickers(instance, sto["x"]),
            "quadratic_objective": instance.quadratic_objective(sto["x"]),
            "shortfall_metric": instance.expected_shortfall_metric(sto["x"]),
        }
    )

    # --- Benders (decomposição real, master relaxado) ---
    t0 = time.perf_counter()
    ben = solve_benders(instance)
    t_ben = time.perf_counter() - t0
    rows.append(
        {
            "method": f"Benders decomposition ({ben['iterations']} iterações)",
            "time_s": t_ben,
            "native_objective": ben["objective"],
            "selected": _x_to_tickers(instance, ben["x"]),
            "x_raw": ben["x"].tolist(),
            "quadratic_objective": instance.quadratic_objective(ben["x"]),
            "shortfall_metric": instance.expected_shortfall_metric(ben["x"]),
        }
    )

    # --- QUBO/QAOA ---
    t0 = time.perf_counter()
    qaoa = solve_with_qaoa(instance, reps=3, maxiter=250)
    t_qaoa = time.perf_counter() - t0
    rows.append(
        {
            "method": "QUBO/QAOA (simulação ideal sem ruído + 1024 shots amostrados)",
            "time_s": t_qaoa,
            "native_objective": qaoa["objective"],
            "selected": _x_to_tickers(instance, qaoa["x"]),
            "quadratic_objective": instance.quadratic_objective(qaoa["x"]),
            "shortfall_metric": instance.expected_shortfall_metric(qaoa["x"]),
        }
    )

    for row in rows:
        row["native_objective_kind"] = (
            "mean_variance" if row["method"].startswith(("Brute", "QUBO")) else "return_plus_shortfall"
        )
    return {
        "track": "model_comparison",
        "instance_tickers": instance.tickers,
        "budget": instance.budget,
        "rows": rows,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Comparação de MODELOS de risco (trilha `model_comparison`, medida — "
        "ver `python -m benchmarks.compare_methods`)",
        "",
        "> Esta tabela NÃO ranqueia algoritmos: LP/MILP/estocástico/Benders otimizam retorno + *shortfall*;",
        "> brute force e QAOA otimizam média-variância. Comparação de algoritmos no MESMO objetivo:",
        "> `results/` (trilha `algorithm_benchmark`, `python -m benchmarks.fair_qubo_benchmark`).",
        "",
        f"Instância: {report['instance_tickers']}, budget={report['budget']} · tempos de UMA execução, sem",
        "distribuição estatística.",
        "",
        "| Método | Tempo (s) | Selecionados | Obj. nativo | Risco quadrático | Shortfall esperado |",
        "|---|---|---|---|---|---|",
    ]
    for r in report["rows"]:
        lines.append(
            f"| {r['method']} | {r['time_s']:.4f} | {', '.join(r['selected'])} | "
            f"{r['native_objective']:.6f} | {r['quadratic_objective']:.6f} | {r['shortfall_metric']:.6f} |"
        )
    lines.append("")
    lines.append(
        "**Nota:** o QAOA usa `qiskit_algorithms.QAOA` com `StatevectorSampler` — o estado é "
        "calculado sem ruído e a saída são 1024 shots AMOSTRADOS dele (não são probabilidades exatas). "
        "Não há hardware quântico. Nesta instância de 3 qubits o QAOA reencontra o ótimo da busca "
        "exaustiva (mesmo objetivo média-variância); MILP/estocástico/Benders escolhem outra carteira "
        "porque otimizam OUTRO objetivo (shortfall), não por erro de nenhum dos lados. O QAOA é o "
        "método mais lento; nada aqui indica vantagem quântica."
    )
    return "\n".join(lines)


if __name__ == "__main__":
    report = run_benchmark()
    md = render_markdown(report)
    out_dir = Path(__file__).parent
    (out_dir / "results.md").write_text(md, encoding="utf-8")
    (out_dir / "results.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=lambda o: float(o)),
        encoding="utf-8",
    )
    print(md)
