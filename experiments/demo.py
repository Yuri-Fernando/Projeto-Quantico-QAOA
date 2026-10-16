"""Demonstrador de 5 passos (auditoria §10) — CLI + relatório HTML estático autocontido.

1. escolhe a instância (domínio, n, k, seed);
2. resolve o baseline clássico exato no MESMO objetivo;
3. gera QUBO, Ising e o circuito QAOA lógico;
4. executa num backend escolhido (ideal exato, Aer com ruído, backend fake; QPU só com opt-in) e
   mostra o circuito físico, SWAPs, profundidade, shots, tempos e histograma;
5. escreve um HTML com f*, f_best, gap, taxa viável, P(ótimo) e a marcação REAL/SIMULADO.

    python -m experiments.demo --domain portfolio --n 6 --mixer xy_ring --p 2 \
        --backend fake --fake-backend generic_heavyhex_d3 --out demo.html
"""
from __future__ import annotations

import argparse
import base64
import html
import io
import json
from pathlib import Path

import numpy as np

from hpc.orchestrator import make_backend, run_pipeline
from optimization.canonical_qubo import x_to_bitstring
from quantum.ansatz import bind, build_qaoa_circuit
from quantum.runner import QAOAConfig

from .analyze import INK_2, SERIES, SURFACE, _style
from .run import make_problem


def _histogram_png(counts: dict, problem, f_star: float, top: int = 16) -> str:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from optimization.canonical_qubo import bitstring_to_x

    items = sorted(counts.items(), key=lambda kv: -kv[1])[:top]
    shots = sum(counts.values())
    colors, labels = [], []
    for key, _ in items:
        x = bitstring_to_x(key)
        if not problem.is_feasible(x):
            colors.append(INK_2)
        elif abs(problem.evaluate(x) - f_star) <= 1e-9 * max(1, abs(f_star)):
            colors.append(SERIES[2])
        else:
            colors.append(SERIES[0])
        labels.append(key)
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    fig.patch.set_facecolor(SURFACE)
    ax.bar(range(len(items)), [c / shots for _, c in items], color=colors, width=0.8)
    ax.set_xticks(range(len(items)), labels, rotation=60, ha="right", fontsize=7, family="monospace")
    _style(ax, f"{top} bitstrings mais frequentes (verde = ótimo, azul = viável, cinza = inviável)", "",
           "frequência")
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=130, facecolor=SURFACE)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def run_demo(args) -> Path:
    problem, _ = make_problem(args.domain, args.n, args.seed, args.k)
    cfg = QAOAConfig(p=args.p, mixer=args.mixer, init_strategy=args.init, maxiter=args.maxiter, seed=args.seed,
                     shots=args.shots, penalty_factor=args.penalty_factor)
    spec = {"ideal": {"type": "ideal_exact"},
            "noisy": {"type": "aer", "regime": "readout+depolarizing"},
            "fake": {"type": "aer", "regime": "backend", "fake_backend": args.fake_backend},
            "qpu": {"type": "ibm_qpu", "backend_name": args.qpu_backend, "dry_run": not args.qpu_submit}}[args.backend]
    backend = make_backend(spec, allow_qpu=args.allow_qpu)
    out = run_pipeline(problem, cfg, backend=backend)
    rec = out["record"]
    ex = rec["execution"] or {}
    metrics = ex.get("metrics") or {}
    logical = build_qaoa_circuit(problem.penalized_qubo(rec["penalty_rho"]).to_ising(), cfg.p, cfg.mixer, cfg.init,
                                 problem.k)
    circuit_text = str(bind(logical, np.array(rec["params_final"])).draw(output="text", fold=120)) \
        if problem.n <= 6 and cfg.p <= 2 else "(circuito omitido: n > 6 ou p > 2; ver métricas)"
    hist = _histogram_png(out["counts"], problem, rec["f_star"]) if out["counts"] else None
    tm = ex.get("transpile_metrics", {})
    real = bool(ex.get("is_real_hardware"))
    rows = [
        ("Instância", f"{problem.domain} · n={problem.n} · k={problem.k} · seed={args.seed}"),
        ("objective_id", problem.objective_id),
        ("Ótimo clássico f* (enumeração)", f"{rec['f_star']:.6f} · {rec['classical_reference']['n_optimal']} ótimo(s)"),
        ("Solução clássica", x_to_bitstring(_optimal_x(problem, rec))),
        ("QAOA", f"mixer {cfg.mixer} · p={cfg.p} · {cfg.optimizer} · init {cfg.init_strategy} · "
                 f"ρ={rec['penalty_rho']:.4g}"),
        ("Backend", f"{ex.get('backend_name')} ({ex.get('backend_type')}) · dispositivo {ex.get('device')}"),
        ("Hardware real?", "SIM" if real else "NÃO — simulação clássica"),
        ("Status", f"{ex.get('status')} · job_id {ex.get('job_id')}"),
        ("f_best (melhor amostra viável)", _f(metrics.get("f_best"))),
        ("gap absoluto", _f(metrics.get("gap_abs"))),
        ("taxa de amostras viáveis", _f(metrics.get("feasible_rate"))),
        ("P(ótimo) amostrado [IC95 Wilson]",
         f"{_f(metrics.get('p_optimum'))} {[round(v, 4) for v in metrics.get('p_optimum_ci95') or []]}"),
        ("P(ótimo) ideal exato", _f(rec.get("p_optimum_exact"))),
        ("P(ótimo) sorteio uniforme viável", _f(rec.get("p_optimum_uniform_feasible"))),
        ("Portas 2Q lógicas → físicas", f"{tm.get('two_qubit_gates_logical')} → {tm.get('two_qubit_gates_physical')}"),
        ("SWAPs inseridos", str(tm.get("swap_count"))),
        ("Profundidade lógica → física", f"{tm.get('depth_logical')} → {tm.get('depth_physical')}"),
        ("Shots", str(cfg.shots)),
        ("Tempos (s)", json.dumps({k: round(v, 4) for k, v in rec["elapsed"].items()}, ensure_ascii=False)),
    ]
    page = _html(rows, circuit_text, hist, ex.get("warnings", []))
    path = Path(args.out)
    path.write_text(page, encoding="utf-8")
    print(f"relatório: {path.resolve()}")
    return path


def _optimal_x(problem, rec):
    from optimization.classical_qubo import solve_enumeration

    return solve_enumeration(problem)["x"]


def _f(v) -> str:
    return "—" if v is None else f"{v:.6f}" if isinstance(v, float) else str(v)


def _html(rows, circuit_text, hist_b64, warnings) -> str:
    trs = "\n".join(f"<tr><th>{html.escape(k)}</th><td>{html.escape(str(v))}</td></tr>" for k, v in rows)
    warn = "".join(f"<li>{html.escape(w)}</li>" for w in warnings) or "<li>nenhum</li>"
    img = f'<img alt="histograma de contagens" src="data:image/png;base64,{hist_b64}">' if hist_b64 else ""
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>QAOA Lab Demo</title>
<style>
:root {{ --bg:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --line:#e4e3df; --accent:#2a78d6; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#1a1a19; --ink:#f0efec; --ink2:#c3c2b7; --line:#3a3936;
  --accent:#3987e5; }} }}
body {{ background:var(--bg); color:var(--ink); font:15px/1.5 system-ui,sans-serif; margin:0; padding:24px 16px; }}
main {{ max-width:960px; margin:0 auto; }}
h1 {{ font-size:22px; margin:0 0 4px; }} p.sub {{ color:var(--ink2); margin:0 0 20px; }}
table {{ border-collapse:collapse; width:100%; }} th,td {{ text-align:left; padding:6px 8px;
  border-bottom:1px solid var(--line); vertical-align:top; }} th {{ color:var(--ink2); font-weight:500; width:38%; }}
pre {{ overflow-x:auto; font-size:11px; border:1px solid var(--line); padding:12px; }}
img {{ max-width:100%; background:#fcfcfb; }} h2 {{ font-size:17px; margin-top:28px; }}
</style></head><body><main>
<h1>Quantum–Classical Optimization Lab — demonstração</h1>
<p class="sub">Relatório gerado por <code>python -m experiments.demo</code>. Mesmo objetivo para clássico e QAOA.</p>
<table>{trs}</table>
<h2>Histograma</h2>{img}
<h2>Circuito lógico (parâmetros otimizados)</h2><pre>{html.escape(circuit_text)}</pre>
<h2>Avisos</h2><ul>{warn}</ul>
</main></body></html>"""


def main(argv=None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--domain", default="portfolio", choices=["portfolio", "shift_scheduling"])
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--k", default="half")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--mixer", default="xy_ring", choices=["x", "xy_ring"])
    ap.add_argument("--p", type=int, default=2)
    ap.add_argument("--init", default="linear_ramp")
    ap.add_argument("--penalty-factor", type=float, default=1.0)
    ap.add_argument("--maxiter", type=int, default=200)
    ap.add_argument("--shots", type=int, default=2048)
    ap.add_argument("--backend", default="fake", choices=["ideal", "noisy", "fake", "qpu"])
    ap.add_argument("--fake-backend", default="generic_heavyhex_d3")
    ap.add_argument("--qpu-backend", default="ibm_brisbane")
    ap.add_argument("--qpu-submit", action="store_true", help="submete job real (sem isso: dry-run)")
    ap.add_argument("--allow-qpu", action="store_true")
    ap.add_argument("--out", default="demo_report.html")
    args = ap.parse_args(argv)
    from quantum.backends import QPUNotAllowed, QPUUnavailable

    try:
        return run_demo(args)
    except (QPUNotAllowed, QPUUnavailable) as exc:
        raise SystemExit(f"QPU não executada: {exc}") from None


if __name__ == "__main__":
    main()
