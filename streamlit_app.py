"""Minimal Streamlit interface for comparing Grok memory substrates."""

from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Iterable

import altair as alt
import pandas as pd
import streamlit as st

from p_adic_memory.simulation import MetricSnapshot, compare_models


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


def _snapshots_to_frame(results: Dict[str, Iterable[MetricSnapshot]]) -> pd.DataFrame:
    rows = []
    for model, snapshots in results.items():
        for snapshot in snapshots:
            data = asdict(snapshot)
            minute = data["minute"]
            rows.append({"minute": minute, "metric": "Recall", "value": data["recall"], "model": model})
            rows.append({"minute": minute, "metric": "Drift", "value": data["drift"], "model": model})
            rows.append({"minute": minute, "metric": "Energy", "value": data["energy"], "model": model})
    frame = pd.DataFrame(rows)
    frame.sort_values(["metric", "minute", "model"], inplace=True)
    return frame


def _render_metric_chart(frame: pd.DataFrame, metric: str) -> None:
    subset = frame[frame["metric"] == metric]
    chart = (
        alt.Chart(subset)
        .mark_line()
        .encode(
            x=alt.X("minute:Q", title="Minutes"),
            y=alt.Y("value:Q", title=metric, stack=None),
            color=alt.Color("model:N", title="Configuration"),
            tooltip=["minute", "value", "model"],
        )
        .interactive()
    )
    st.altair_chart(chart, use_container_width=True)


if run_button:
    with placeholder, st.spinner("Running 25-minute conversation simulation..."):
        results = compare_models()
    placeholder.success("Simulation complete.")
    frame = _snapshots_to_frame(results)
    with chart_container:
        _render_metric_chart(frame, "Recall")
        _render_metric_chart(frame, "Drift")
        _render_metric_chart(frame, "Energy")
else:
    placeholder.info("Press 'Run test' to generate comparison charts.")
