"""Gera ``summary.md`` e figuras a partir de ``records.jsonl`` — nunca reexecuta experimento.

Regra da auditoria (§12): tabelas e gráficos são regenerados SOMENTE a partir de dados salvos.
ICs: bootstrap percentil 95% sobre execuções independentes (seeds × instâncias).

Uso:  python -m experiments.analyze results/<experimento>/<run_id>
"""
from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from quantum.measurement import bootstrap_ci

from .schemas import read_manifest, read_records

# Paleta de referência (skill dataviz): 3 primeiros slots categóricos + tintas neutras.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
INK, INK_2, GRID, SURFACE, BASELINE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb", "#8a8984"


# --------------------------------------------------------------------------- utilitários
def _fmt(v, digits=4) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    if isinstance(v, (bool, np.bool_)):
        return "sim" if v else "não"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)):
        if v != 0 and (abs(v) < 1e-3 or abs(v) >= 1e5):
            return f"{v:.2e}"
        return f"{v:.{digits}f}"
    return str(v)


def md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_sem dados_\n"
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(_fmt(row[c]) for c in cols) + " |")
    return "\n".join(lines) + "\n"


def mean_ci(values: Sequence) -> str:
    vals = [float(v) for v in values if v is not None and not (isinstance(v, float) and np.isnan(v))]
    if not vals:
        return "—"
    lo, hi = bootstrap_ci(vals, seed=0)
    return f"{np.mean(vals):.4f} [{lo:.4f}, {hi:.4f}]"


def aggregate(df: pd.DataFrame, keys: list[str], metrics: dict[str, Callable]) -> pd.DataFrame:
    rows = []
    for key, g in df.groupby(keys, dropna=False, sort=True):
        key = key if isinstance(key, tuple) else (key,)
        row = dict(zip(keys, key))
        row["runs"] = len(g)
        for name, fn in metrics.items():
            row[name] = fn(g)
        rows.append(row)
    return pd.DataFrame(rows)


def _style(ax, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_facecolor(SURFACE)
    ax.set_title(title, color=INK, fontsize=11, loc="left")
    ax.set_xlabel(xlabel, color=INK_2, fontsize=9)
    ax.set_ylabel(ylabel, color=INK_2, fontsize=9)
    ax.tick_params(colors=INK_2, labelsize=8)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(BASELINE)


def _figure(ncols=1, width=6.4, height=3.6):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, ncols, figsize=(width * ncols if ncols > 1 else width, height), squeeze=False)
    fig.patch.set_facecolor(SURFACE)
    return fig, axes[0], plt


def _save(fig, plt, path: Path) -> str:
    path.parent.mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    return path.name


def _flatten(records: list[dict]) -> pd.DataFrame:
    return pd.json_normalize(records, sep=".")


# --------------------------------------------------------------------------- por tipo
def summarize_equivalence(df: pd.DataFrame, out: Path) -> str:
    cols = ["domain", "n", "k", "instance_seed", "max_abs_f_vs_original", "max_abs_qubo_vs_f_plus_penalty",
            "max_abs_ising_vs_qubo", "max_abs_pauli_vs_qubo", "abs_diff_milp_vs_enumeration", "lp_le_milp",
            "critical_penalty", "safe_penalty", "qubo_ground_state_is_optimal", "pass"]
    cols = [c for c in cols if c in df]
    ok = int(df["pass"].sum())
    return f"**Paridade:** {ok}/{len(df)} instâncias passaram em todas as checagens.\n\n" + md_table(df[cols])


def summarize_benchmark(df: pd.DataFrame, out: Path) -> str:
    parts = []
    qa = df[df["algorithm"].astype(str).str.startswith("qaoa")].copy()
    cl = df[~df["algorithm"].astype(str).str.startswith("qaoa")].copy()
    if not cl.empty:
        cl_agg = aggregate(cl, ["domain", "n", "algorithm"], {
            "taxa_ótimo": lambda g: g["is_optimal"].mean() if "is_optimal" in g and g["is_optimal"].notna().any()
            else (1.0 if g["algorithm"].iloc[0] in ("enumeration", "milp_linearized") else None),
            "gap_abs_médio": lambda g: g["gap_abs"].mean() if "gap_abs" in g else None,
            "P(ótimo)_amostra": lambda g: g["p_optimum"].mean() if "p_optimum" in g else None,
            "tempo_s_médio": lambda g: g["time_s"].mean(),
        })
        parts.append("### Baselines clássicos (mesmo objetivo)\n\n" + md_table(cl_agg))
    if not qa.empty:
        keys = [k for k in ("domain", "n", "algorithm", "p", "optimizer", "init_strategy", "penalty_factor",
                            "objective_mode", "shots") if k in qa and qa[k].nunique(dropna=False) >= 1]
        varying = [k for k in keys if qa[k].nunique(dropna=False) > 1 or k in ("domain", "n", "algorithm", "p")]
        qa["p"] = qa["p"].astype(int)
        qa["ratio_vs_uniform"] = qa["p_optimum_exact"] / qa["p_optimum_uniform_feasible"]
        # Métricas EXATAS dependem só da otimização: seeds que geram os mesmos parâmetros finais
        # (ex.: inicialização determinística + objetivo exato) são pseudo-réplicas e contam uma vez.
        qa["_replica"] = qa["instance_hash"] + "|" + qa["params_final"].map(lambda v: str(np.round(v, 10).tolist()))
        uniq = lambda g: g.drop_duplicates("_replica")  # noqa: E731
        q_agg = aggregate(qa, varying, {
            "indep.": lambda g: uniq(g).shape[0],
            "P(ótimo) exato [IC95]": lambda g: mean_ci(uniq(g)["p_optimum_exact"]),
            "÷ uniforme viável": lambda g: uniq(g)["ratio_vs_uniform"].mean(),
            "P(viável) exato": lambda g: uniq(g)["p_feasible_exact"].mean(),
            "melhor amostra ótima": lambda g: g["ideal_sampling.is_optimal"].mean(),
            "avaliações": lambda g: g["circuit_evaluations"].mean(),
            "tempo_total_s": lambda g: g["elapsed.time_total"].mean(),
        })
        parts.append("### QAOA (simulação ideal exata + amostragem finita)\n\n"
                     "`÷ uniforme viável` = P(ótimo) exato dividido pela probabilidade de sortear um ótimo "
                     "uniformemente entre as C(n,k) seleções viáveis (baseline aleatório). Valores ≤ 1 significam "
                     "que o circuito não concentrou probabilidade no ótimo. `runs` = execuções; `indep.` = "
                     "otimizações distintas (pseudo-réplicas removidas das métricas exatas e do IC). "
                     "`melhor amostra ótima` = fração de execuções cuja melhor amostra viável é ótima — compare com "
                     "`random_feasible_sampling`, que usa o MESMO número de amostras.\n\n" + md_table(q_agg))
        if "elapsed.time_total" in qa and "memory.peak_traced_mb" in qa:
            mem = aggregate(qa, ["domain", "n", "algorithm"], {
                "statevector_teórico_MB": lambda g: g["resources.statevector_bytes"].iloc[0] / 2**20,
                "pico_tracemalloc_MB": lambda g: g["memory.peak_traced_mb"].max(),
                "tempo_otimização_s": lambda g: g["elapsed.time_classical_opt"].mean(),
                "2Q_lógicas_total": lambda g: g["resources.logical_two_qubit_gates_total"].mean(),
            })
            parts.append("### Recursos (QAOA)\n\n" + md_table(mem))
        parts.append(_benchmark_figures(qa, cl, out))
    return "\n".join(parts)


def _benchmark_figures(qa: pd.DataFrame, cl: pd.DataFrame, out: Path) -> str:
    md = []
    for domain, gd in qa.groupby("domain"):
        init_note = ""
        if "init_strategy" in gd and (gd["init_strategy"] == "random").any() and gd["init_strategy"].nunique() > 1:
            gd = gd[gd["init_strategy"] == "random"]
            init_note = " — inicialização aleatória"
        ps = sorted(gd["p"].unique())
        fig, axes, plt = _figure(ncols=len(ps), width=3.4, height=3.2)
        for ax, p in zip(axes, ps):
            gp = gd[gd["p"] == p]
            for color, (alg, ga) in zip(SERIES, gp.groupby("algorithm")):
                agg = ga.groupby("n")["p_optimum_exact"].agg(["mean", "std"]).reset_index()
                ax.plot(agg["n"], agg["mean"], color=color, linewidth=2, marker="o", markersize=5,
                        label=alg.replace("qaoa_", "mixer "))
            base = gp.groupby("n")["p_optimum_uniform_feasible"].mean()
            ax.plot(base.index, base.values, color=INK_2, linewidth=1.5, linestyle="--", label="uniforme viável")
            ax.set_yscale("log")
            _style(ax, f"p = {p}", "n (variáveis)", "P(ótimo) exato" if p == ps[0] else "")
        axes[0].legend(frameon=False, fontsize=8, labelcolor=INK_2)
        fig.suptitle(f"{domain}: P(ótimo) vs. tamanho (média das seeds{init_note})", color=INK, fontsize=11,
                     x=0.01, ha="left")
        md.append(f"![P(ótimo) {domain}](figures/{_save(fig, plt, out / 'figures' / f'p_opt_vs_n_{domain}.png')})")

        fig, axes, plt = _figure()
        ax = axes[0]
        series = [("QAOA mixer x (total)", gd[gd["algorithm"] == "qaoa_x"], "elapsed.time_total"),
                  ("QAOA mixer xy_ring (total)", gd[gd["algorithm"] == "qaoa_xy_ring"], "elapsed.time_total")]
        cld = cl[cl["domain"] == domain]
        for color, (label, g, col) in zip(SERIES, series):
            if not g.empty:
                t = g.groupby("n")[col].median()
                ax.plot(t.index, t.values, color=color, linewidth=2, marker="o", markersize=5, label=label)
        for style, alg in (("--", "enumeration"), (":", "milp_linearized")):
            t = cld[cld["algorithm"] == alg].groupby("n")["time_s"].median()
            if not t.empty:
                ax.plot(t.index, t.values, color=INK_2, linewidth=1.5, linestyle=style, label=alg)
        ax.set_yscale("log")
        _style(ax, f"{domain}: tempo de parede (mediana) — simulação CPU, não é QPU", "n (variáveis)", "segundos")
        ax.legend(frameon=False, fontsize=8, labelcolor=INK_2)
        md.append(f"![tempo {domain}](figures/{_save(fig, plt, out / 'figures' / f'time_vs_n_{domain}.png')})")
    return "\n\n".join(md) + "\n"


def summarize_transpilation(df: pd.DataFrame, out: Path) -> str:
    agg = aggregate(df, ["domain", "mixer", "p", "backend_family", "optimization_level", "n"], {
        "2Q_lógicas": lambda g: g["two_qubit_gates_logical"].mean(),
        "2Q_físicas": lambda g: g["two_qubit_gates_physical"].mean(),
        "SWAPs": lambda g: g["swap_count"].mean(),
        "depth_lógica": lambda g: g["depth_logical"].mean(),
        "depth_física": lambda g: g["depth_physical"].mean(),
        "depth_2Q_física": lambda g: g["depth_two_qubit_physical"].mean(),
        "tempo_transpile_s": lambda g: g["transpile_time_s"].mean(),
        "Target_ok": lambda g: bool(g["target_supported"].all()),
    })
    md = [md_table(agg)]
    for domain, gd in df.groupby("domain"):
        sub = gd[(gd["p"] == gd["p"].min()) & (gd["optimization_level"] == gd["optimization_level"].max())]
        mixers = sorted(sub["mixer"].unique())
        fig, axes, plt = _figure(ncols=len(mixers), width=3.6, height=3.2)
        for ax, mixer in zip(axes, mixers):
            gm = sub[sub["mixer"] == mixer]
            fams = [f for f in gm["backend_family"].unique() if "all_to_all" not in f]
            for color, fam in zip(SERIES, sorted(fams)):
                t = gm[gm["backend_family"] == fam].groupby("n")["swap_count"].mean()
                ax.plot(t.index, t.values, color=color, linewidth=2, marker="o", markersize=5, label=fam)
            _style(ax, f"mixer {mixer}", "n (qubits lógicos)", "SWAPs inseridos" if mixer == mixers[0] else "")
        axes[0].legend(frameon=False, fontsize=8, labelcolor=INK_2)
        fig.suptitle(f"{domain}: SWAPs do roteamento (p mínimo, nível máximo; média das seeds)", color=INK,
                     fontsize=11, x=0.01, ha="left")
        md.append(f"![SWAPs {domain}](figures/{_save(fig, plt, out / 'figures' / f'swaps_vs_n_{domain}.png')})")
    return "\n\n".join(md) + "\n"


def summarize_noise(df: pd.DataFrame, out: Path) -> str:
    keys = [k for k in ("domain", "n", "algorithm", "mixer", "p", "regime_label") if k in df]
    agg = aggregate(df, keys, {
        "P(ótimo) amostrado [IC95]": lambda g: mean_ci(g["p_optimum"]),
        "P(ótimo) ideal exato": lambda g: g["ideal_reference.p_optimum_exact"].mean(),
        "taxa_viável [IC95]": lambda g: mean_ci(g["feasible_rate"]),
        "melhor amostra ótima": lambda g: g["is_optimal"].mean(),
        "2Q_físicas": lambda g: g["execution.transpile_metrics.two_qubit_gates_physical"].mean(),
        "SWAPs": lambda g: g["execution.transpile_metrics.swap_count"].mean(),
    })
    md = [md_table(agg)]
    order = list(dict.fromkeys(df["regime_label"]))
    for (domain, n), gd in df.groupby(["domain", "n"]):
        if n != df["n"].max():
            continue
        fig, axes, plt = _figure(ncols=2, width=3.8, height=3.4)
        mixers = sorted(gd["mixer"].unique())
        width = 0.8 / max(1, len(mixers))
        x = np.arange(len(order))
        for col, (metric, label) in enumerate((("feasible_rate", "taxa de amostras viáveis"),
                                               ("p_optimum", "P(ótimo) amostrado"))):
            ax = axes[col]
            for i, (color, mixer) in enumerate(zip(SERIES, mixers)):
                means = [gd[(gd["mixer"] == mixer) & (gd["regime_label"] == r)][metric].mean() for r in order]
                ax.bar(x + i * width - 0.4 + width / 2, means, width=width * 0.92, color=color, label=f"mixer {mixer}")
            ax.set_xticks(x, order, rotation=35, ha="right", fontsize=7)
            _style(ax, label, "", "")
        axes[0].legend(frameon=False, fontsize=8, labelcolor=INK_2)
        fig.suptitle(f"{domain}, n={n}: mesmo circuito otimizado no ideal, executado sob ruído (média das seeds)",
                     color=INK, fontsize=10, x=0.01, ha="left")
        md.append(f"![ruído {domain}](figures/{_save(fig, plt, out / 'figures' / f'noise_{domain}_n{n}.png')})")
    return "\n\n".join(md) + "\n"


def summarize_devices(df: pd.DataFrame, out: Path) -> str:
    det = df[df["record_type"] == "device_detection"]
    ex = df[df["record_type"] == "execution"]
    md = []
    if not det.empty:
        d = det.iloc[0]
        md.append(f"- GPU NVIDIA no host: `{d.get('nvidia_gpus')}`\n- `AerSimulator().available_devices()`: "
                  f"`{d.get('aer_available_devices')}`\n- Status: **{d.get('gpu_status')}**\n")
    cols = [c for c in ("n", "requested_device", "status", "device_used", "time_execution_median_s",
                        "statevector_bytes", "reason") if c in ex]
    md.append(md_table(ex[cols]))
    return "\n".join(md)


def summarize_qpu(df: pd.DataFrame, out: Path) -> str:
    cols = [c for c in ("backend_name", "n", "k", "dry_run", "shots", "status", "reason", "is_real_hardware")
            if c in df]
    return md_table(df[cols])


SUMMARIZERS = {"equivalence": summarize_equivalence, "algorithm_benchmark": summarize_benchmark,
               "transpilation": summarize_transpilation, "noise": summarize_noise, "devices": summarize_devices,
               "qpu": summarize_qpu}


def analyze_run(run_dir: Path) -> Path:
    run_dir = Path(run_dir)
    manifest = read_manifest(run_dir)
    records = list(read_records(run_dir))
    df = _flatten(records)
    body = SUMMARIZERS[manifest["kind"]](df, run_dir) if records else "_nenhum registro_\n"
    dev = manifest.get("devices", {})
    header = [
        f"# {manifest['experiment']} — resumo gerado de `records.jsonl`",
        "",
        f"- run_id: `{manifest['run_id']}` · kind: `{manifest['kind']}` · track: `{manifest['track']}`",
        f"- commit: `{manifest.get('git_sha')}` (working tree suja: {manifest.get('git_dirty')})",
        f"- config_hash: `{manifest['config_hash'][:16]}` · registros: {manifest.get('n_records', len(records))}"
        f" · tempo de parede: {manifest.get('wall_time_s', 0):.1f}s"
        f" · modo quick: {manifest['config'].get('quick_mode', False)}",
        f"- Python {manifest['python_version']} · qiskit {manifest['library_versions'].get('qiskit')} · "
        f"qiskit-aer {manifest['library_versions'].get('qiskit-aer')} · GPU: {dev.get('gpu_status')}",
        "- Toda execução quântica aqui é SIMULAÇÃO em CPU (`is_real_hardware=false`), salvo indicação explícita.",
        "",
    ]
    path = run_dir / "summary.md"
    path.write_text("\n".join(header) + body, encoding="utf-8")
    return path


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(analyze_run(Path(arg)))
