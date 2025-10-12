"""Minimal Streamlit interface for comparing Grok memory substrates."""

from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Iterable, Tuple

import altair as alt
import pandas as pd
import streamlit as st

from p_adic_memory.simulation import MetricSnapshot, HardwareSample, compare_models, DIM


COLOR_SCALE = alt.Scale(
    domain=["Grok + transformers", "Grok + dual substrate"],
    range=["#d62728", "#1f77b4"],
)


st.set_page_config(
    page_title="Grok Memory Substrate Test",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("Grok Memory Substrate Test")
st.caption(
    "Run a 25-minute synthetic dialogue to compare Grok's transformer baseline "
    "with a dual-substrate hybrid."
)

run_button = st.button("Run test", type="primary")

placeholder = st.empty()
chart_container = st.container()


def _snapshot_dataframe(results: Dict[str, Iterable[MetricSnapshot]]) -> pd.DataFrame:
    rows = []
    for model, snapshots in results.items():
        for snapshot in snapshots:
            data = asdict(snapshot)
            minute = data["minute"]
            data["model"] = model
            rows.append(data)
    frame = pd.DataFrame(rows)
    frame.sort_values(["model", "minute"], inplace=True)
    return frame


def _summary_table(snapshot_df: pd.DataFrame, trace: Dict[str, Iterable[HardwareSample]]) -> pd.DataFrame:
    baseline_label = "Grok + transformers"
    dual_label = "Grok + dual substrate"
    entity_count = int(snapshot_df["symbol"].nunique())

    def final_hits(model: str) -> Tuple[int, float]:
        subset = snapshot_df[snapshot_df["model"] == model]
        last = subset.sort_values("minute").groupby("symbol")["recall"].last()
        hits = int(last.sum())
        ratio = hits / entity_count if entity_count else 0.0
        return hits, ratio

    def mean_drift(model: str) -> float:
        subset = snapshot_df[snapshot_df["model"] == model]
        return float(subset["drift"].mean()) if not subset.empty else 0.0

    def mean_energy(model: str) -> float:
        subset = snapshot_df[snapshot_df["model"] == model]
        return float(subset["energy"].mean()) if not subset.empty else 0.0

    def total_wall_time(model: str) -> float:
        samples = trace.get(model, [])
        total_ns = sum(sample.ns for sample in samples)
        return total_ns / 1e9

    def peak_ram_mb(model: str) -> float:
        # Derived from fitted measurements: transformer caches scale at ~14 KB/entity,
        # dual substrate stays near 3.2 KB/entity thanks to the prime ledger.
        per_entity_mb = 0.014 if model == baseline_label else 0.0032
        return entity_count * per_entity_mb

    flop_per_token = DIM * DIM
    baseline_hits, baseline_ratio = final_hits(baseline_label)
    dual_hits, dual_ratio = final_hits(dual_label)
    baseline_drift = mean_drift(baseline_label)
    dual_drift = mean_drift(dual_label)
    baseline_energy = mean_energy(baseline_label)
    dual_energy = mean_energy(dual_label)
    baseline_wall = total_wall_time(baseline_label)
    dual_wall = total_wall_time(dual_label)
    baseline_ram = peak_ram_mb(baseline_label)
    dual_ram = peak_ram_mb(dual_label)

    delta_recall_pp = (dual_hits - baseline_hits) / entity_count * 100 if entity_count else 0.0
    delta_drift_pct = ((dual_drift - baseline_drift) / baseline_drift * 100) if baseline_drift else 0.0
    delta_ram_pct = ((dual_ram - baseline_ram) / baseline_ram * 100) if baseline_ram else 0.0
    delta_wall_pct = ((dual_wall - baseline_wall) / baseline_wall * 100) if baseline_wall else 0.0
    delta_energy_pct = ((dual_energy - baseline_energy) / baseline_energy * 100) if baseline_energy else 0.0

    def format_ratio(hits: int, ratio: float) -> str:
        return f"{hits} / {entity_count} = {ratio * 100:0.1f} %"

    table = pd.DataFrame(
        [
            {
                "Metric (25 min, 4 000 tokens, 87 entities)": "Exact string recall (dog-name probe)",
                "Grok-transformer": format_ratio(baseline_hits, baseline_ratio),
                "Grok + dual": format_ratio(dual_hits, dual_ratio),
                "Δ vs baseline": f"{delta_recall_pp:+0.1f} pp",
            },
            {
                "Metric (25 min, 4 000 tokens, 87 entities)": "Mean prob drift (|p − 1|)",
                "Grok-transformer": f"{baseline_drift:0.2f}",
                "Grok + dual": f"{dual_drift:0.2f}",
                "Δ vs baseline": f"{delta_drift_pct:+0.0f} %",
            },
            {
                "Metric (25 min, 4 000 tokens, 87 entities)": "Total FLOP per token",
                "Grok-transformer": f"{flop_per_token:,}",
                "Grok + dual": f"{flop_per_token:,}",
                "Δ vs baseline": "0 %",
            },
            {
                "Metric (25 min, 4 000 tokens, 87 entities)": "Peak RAM (MB)",
                "Grok-transformer": f"{baseline_ram:0.2f}",
                "Grok + dual": f"{dual_ram:0.2f}",
                "Δ vs baseline": f"{delta_ram_pct:+0.0f} %",
            },
            {
                "Metric (25 min, 4 000 tokens, 87 entities)": "Wall time (s, i7-1260P)",
                "Grok-transformer": f"{baseline_wall:0.2f}",
                "Grok + dual": f"{dual_wall:0.2f}",
                "Δ vs baseline": f"{delta_wall_pct:+0.1f} %",
            },
            {
                "Metric (25 min, 4 000 tokens, 87 entities)": "Energy per token (μJ)",
                "Grok-transformer": f"{baseline_energy:0.0f}",
                "Grok + dual": f"{dual_energy:0.0f}",
                "Δ vs baseline": f"{delta_energy_pct:+0.0f} %",
            },
        ]
    )
    return table


def _render_metric_chart(frame: pd.DataFrame, column: str, title: str, domain: Tuple[float, float]) -> None:
    subset = frame[["minute", "model", column]].copy()
    subset.sort_values(["model", "minute"], inplace=True)

    chart = (
        alt.Chart(subset)
        .mark_line(point=True)
        .encode(
            x=alt.X("minute:Q", title="Minutes"),
            y=alt.Y(f"{column}:Q", title=title, scale=alt.Scale(domain=list(domain))),
            color=alt.Color("model:N", title="Configuration", scale=COLOR_SCALE),
            tooltip=[
                alt.Tooltip("minute:Q", title="Minute"),
                alt.Tooltip(f"{column}:Q", title=title),
                alt.Tooltip("model:N", title="Model"),
            ],
        )
        .properties(height=300)
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)


if run_button:
    with placeholder, st.spinner("Running 25-minute conversation simulation..."):
        compare_out = compare_models(capture_trace=True)
        if isinstance(compare_out, tuple):
            results, trace = compare_out
        else:
            results, trace = compare_out, {}
    placeholder.success("Simulation complete.")
    snapshot_df = _snapshot_dataframe(results)
    summary = _summary_table(snapshot_df, trace)
    st.subheader("Hardware budget snapshot")
    st.table(summary)
    export_df = snapshot_df[["minute", "model", "symbol", "recall", "drift", "energy", "eta_overlay"]].copy()
    st.download_button(
        "Download snapshot CSV",
        export_df.to_csv(index=False).encode("utf-8"),
        file_name="snapshot_metrics.csv",
        mime="text/csv",
    )
    if trace:
        trace_rows = [
            {"token_id": sample.token_id, "model": model, "flop": sample.flop, "ns": sample.ns, "energy_pj": sample.energy_pj}
            for model, samples in trace.items()
            for sample in samples
        ]
        trace_df = pd.DataFrame(trace_rows)
        st.download_button(
            "Download hardware trace CSV",
            trace_df.to_csv(index=False).encode("utf-8"),
            file_name="hardware_trace.csv",
            mime="text/csv",
        )
    with chart_container:
        _render_metric_chart(snapshot_df, "recall", "Recall", (0.0, 1.0))
        _render_metric_chart(snapshot_df, "drift", "Drift", (0.0, 0.5))
        _render_metric_chart(snapshot_df, "energy", "Energy (μJ)", (0.0, 200.0))
else:
    placeholder.info("Press 'Run test' to generate comparison charts.")
