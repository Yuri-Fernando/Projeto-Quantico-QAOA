"""Benchmark real: LP vs MILP vs Estocástico vs Benders vs QAOA, na mesma instância.

Mede, para cada método, tempo de execução (``time.perf_counter``), o valor
objetivo nativo do método, e reavalia a solução ``x`` encontrada nas DUAS
métricas comuns definidas em ``optimization.instance``:

- ``quadratic_objective``: risco média-variância (nativo do QUBO/QAOA)
- ``expected_shortfall_metric``: risco de shortfall por cenário (nativo
  de LP/MILP/estocástico/Benders)

Isso permite comparar "qualidade da solução" de forma honesta mesmo entre
métodos que otimizam objetivos formalmente diferentes. Os números deste
relatório são MEDIDOS a cada execução — nenhum valor é inventado.

Uso:
    python -m benchmarks.compare_methods
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from optimization.instance import build_instance, brute_force_optimum
from optimization.lp import solve_lp_relaxation
from optimization.milp import solve_milp
from optimization.stochastic import solve_stochastic_extensive_form
from optimization.benders import solve_benders
from optimization.qaoa import solve_with_qaoa


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
            "method": "QUBO/QAOA (simulado, statevector exato)",
            "time_s": t_qaoa,
            "native_objective": qaoa["objective"],
            "selected": _x_to_tickers(instance, qaoa["x"]),
            "quadratic_objective": instance.quadratic_objective(qaoa["x"]),
            "shortfall_metric": instance.expected_shortfall_metric(qaoa["x"]),
        }
    )

    return {"instance_tickers": instance.tickers, "budget": instance.budget, "rows": rows}


def render_markdown(report: dict) -> str:
    lines = [
        "# Resultados do benchmark (medidos — ver `python -m benchmarks.compare_methods`)",
        "",
        f"Instância: {report['instance_tickers']}, budget={report['budget']}",
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
        "**Nota honesta:** o QAOA aqui roda em simulador estatevector local (sem ruído, "
        "sem hardware quântico real). Ele NÃO tem nenhuma vantagem de tempo sobre os métodos "
        "clássicos nesta instância de 3 qubits — pelo contrário, é o método mais lento do "
        "benchmark. O objetivo desta comparação é validar CORREÇÃO (QAOA encontra o mesmo "
        "ótimo que busca exaustiva / MILP), não demonstrar vantagem quântica, que não existe "
        "nesta escala nem nesta configuração."
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
