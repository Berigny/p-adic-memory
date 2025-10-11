"""Lightweight Streamlit front-end backed by the declarative spec."""

from __future__ import annotations

import csv
import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import streamlit as st

from p_adic_memory.streamlit_spec import get_streamlit_spec


SPEC = get_streamlit_spec()
REPO_ROOT = Path(__file__).resolve().parent
RESULTS_PATH = REPO_ROOT / "results.csv"


def _to_int(value: Optional[Any]) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _to_float(value: Optional[Any]) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return bool(value)
    lowered = str(value).strip().lower()
    if lowered in {"true", "t", "1", "yes", "y"}:
        return True
    if lowered in {"false", "f", "0", "no", "n"}:
        return False
    return None


@st.cache_data(show_spinner=False)
def load_results() -> List[Dict[str, Any]]:
    if not RESULTS_PATH.exists():
        return []

    rows: List[Dict[str, Any]] = []
    with RESULTS_PATH.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for raw in reader:
            model = raw.get("model", "").strip()
            log_path = (raw.get("log_path") or "").strip()
            tokens = _to_int(raw.get("tokens"))
            elapsed = _to_float(raw.get("elapsed_s"))
            rows.append(
                {
                    "model": model,
                    "log_path": log_path or None,
                    "cycle": _to_int(raw.get("cycle")),
                    "continuous_dim": _to_int(raw.get("continuous_dim")),
                    "drift_rate": _to_float(raw.get("drift_rate")),
                    "elapsed_s": elapsed,
                    "ledger_bits": _to_int(raw.get("ledger_bits")),
                    "ops": _to_int(raw.get("ops")),
                    "ops_proxy": _to_float(raw.get("ops_proxy")),
                    "recall_at_1": _to_float(raw.get("recall@1")),
                    "retention_half_life": _to_float(raw.get("retention_half_life")),
                    "shuffle": _to_bool(raw.get("shuffle")),
                    "step": _to_int(raw.get("step")),
                    "symbols": _to_int(raw.get("symbols")),
                    "tokens": tokens,
                    "tokens_per_s": _to_float(raw.get("tokens_per_s")),
                    "record_type": raw.get("type", "").strip(),
                    "time_per_token": (elapsed / tokens) if elapsed and tokens else None,
                }
            )
    return rows


@st.cache_data(show_spinner=False)
def load_log_records(log_path: str) -> List[Dict[str, Any]]:
    path = (REPO_ROOT / log_path).resolve()
    if not path.exists():
        return []

    records: List[Dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "turn" in record:
                record["turn"] = _to_int(record.get("turn"))
            if "ops" in record:
                record["ops"] = _to_int(record.get("ops"))
            if "ledger_flag" in record:
                record["ledger_flag"] = bool(record.get("ledger_flag"))
            records.append(record)
    return records


MODEL_ALIAS: Dict[str, Set[str]] = {
    "dual-substrate": {"dual_substrate", "dual_substrate_demo"},
    "transformer": {"baseline_transformer"},
    "NoLiMa": {"nolima_baseline"},
}


def _matching_models(selected: Optional[str]) -> Optional[Set[str]]:
    if not selected:
        return None
    return MODEL_ALIAS.get(selected, {selected})


def filter_results(results: List[Dict[str, Any]], selected_model: Optional[str]) -> List[Dict[str, Any]]:
    if not results:
        return []
    targets = _matching_models(selected_model)
    if not targets:
        return list(results)
    return [row for row in results if row.get("model") in targets]


def _run_label(row: Dict[str, Any]) -> str:
    model = row.get("model", "?")
    log_path = row.get("log_path") or ""
    stem = Path(log_path).stem if log_path else ""
    return f"{model} ({stem})" if stem else model


def retention_curve_data(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    for row in results:
        turns = row.get("tokens")
        recall = row.get("recall_at_1")
        if turns is None or recall is None:
            continue
        data.append({"turns": turns, "Recall@1": recall, "model": row.get("model")})
    data.sort(key=lambda item: (item["model"], item["turns"]))
    return data


def drift_timeline_data(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    for row in results:
        turns = row.get("tokens")
        drift = row.get("drift_rate")
        if turns is None or drift is None:
            continue
        data.append({"turns": turns, "contradiction rate": drift, "model": row.get("model")})
    return data


def efficiency_data(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    for row in results:
        turns = row.get("tokens")
        if turns is None:
            continue
        ops_proxy = row.get("ops_proxy")
        if ops_proxy is not None:
            data.append(
                {
                    "turns": turns,
                    "metric": "ops proxy",
                    "value": ops_proxy,
                    "model": row.get("model"),
                }
            )
        time_per_token = row.get("time_per_token")
        if time_per_token is not None:
            data.append(
                {
                    "turns": turns,
                    "metric": "time/token",
                    "value": time_per_token,
                    "model": row.get("model"),
                }
            )
    return data


def ledger_growth_data(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    for row in results:
        log_path = row.get("log_path")
        if not log_path:
            continue
        records = load_log_records(log_path)
        writes = 0
        ledger_bits = 0
        for record in records:
            if record.get("type") not in {"write", "filler"}:
                continue
            if not record.get("ledger_flag"):
                continue
            writes += 1
            ledger_bits += 1
            data.append({"writes": writes, "bit-length(L)": ledger_bits, "run": _run_label(row)})
    return data


def probe_confusion_data(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    totals: Dict[tuple[str, str], List[int]] = defaultdict(lambda: [0, 0])
    for row in results:
        log_path = row.get("log_path")
        if not log_path:
            continue
        for record in load_log_records(log_path):
            if record.get("type") != "probe":
                continue
            probe = record.get("name") or record.get("probe") or record.get("probe_id")
            if not probe:
                continue
            key = (row.get("model", "?"), str(probe))
            totals[key][0] += 1
            if record.get("ledger_flag"):
                totals[key][1] += 1
    data: List[Dict[str, Any]] = []
    for (model, probe), (count, flagged) in totals.items():
        rate = flagged / count if count else 0.0
        data.append({"model": model, "probe": probe, "rate": rate})
    return data


def entity_recall_data(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    for row in results:
        log_path = row.get("log_path")
        if not log_path:
            continue
        for record in load_log_records(log_path):
            if record.get("type") != "checkpoint":
                continue
            entity = record.get("symbol") or record.get("target") or record.get("name")
            checkpoint = record.get("name") or record.get("qid") or f"t={record.get('turn')}"
            success = 1.0 if record.get("ledger_flag") else 0.0
            data.append(
                {
                    "entity": str(entity),
                    "checkpoint": str(checkpoint),
                    "success": success,
                    "run": _run_label(row),
                }
            )
    return data


def energy_data(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    for row in results:
        ops_proxy = row.get("ops_proxy")
        if ops_proxy is None:
            continue
        data.append({"model": row.get("model"), "avg energy": ops_proxy, "tokens": row.get("tokens")})
    return data


def comparison_table(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    columns = (
        "model",
        "recall_at_1",
        "drift_rate",
        "retention_half_life",
        "ops_proxy",
        "tokens_per_s",
        "ops",
    )
    table: List[Dict[str, Any]] = []
    for row in results:
        entry = {key: row.get(key) for key in columns}
        entry["tokens"] = row.get("tokens")
        table.append(entry)
    return table


def _render_throughput_gauge(results: List[Dict[str, Any]]) -> None:
    st.subheader("Throughput gauge")
    if not results:
        st.info("No throughput measurements available for the current selection.")
        return

    fastest = max(results, key=lambda row: row.get("tokens_per_s") or 0)
    longest = max(results, key=lambda row: row.get("elapsed_s") or 0)
    latest = max(results, key=lambda row: row.get("tokens") or 0)

    col1, col2, col3 = st.columns(3)
    tokens_per_s = fastest.get("tokens_per_s")
    if tokens_per_s:
        col1.metric("Tokens/sec", f"{tokens_per_s:,.2f}", help=_run_label(fastest))
    else:
        col1.metric("Tokens/sec", "—")

    turns_per_s = fastest.get("tokens_per_s")
    if turns_per_s:
        col2.metric("Turns/sec", f"{turns_per_s:,.2f}", help=_run_label(fastest))
    else:
        col2.metric("Turns/sec", "—")

    elapsed = longest.get("elapsed_s") or latest.get("elapsed_s")
    if elapsed:
        col3.metric("Wall-clock (s)", f"{elapsed:,.2f}", help=_run_label(longest))
    else:
        col3.metric("Wall-clock (s)", "—")


def _render_event_log(results: List[Dict[str, Any]]) -> None:
    st.subheader("Event log viewer")
    log_options = [row for row in results if row.get("log_path")]
    if not log_options:
        st.info("No log files available for the selected configuration.")
        return

    labels = [f"{_run_label(row)}" for row in log_options]
    choice = st.selectbox(
        "Choose a run to inspect",
        options=list(range(len(labels))),
        format_func=lambda idx: labels[idx],
        key="event_log_choice",
    )
    selected = log_options[int(choice)]
    records = [rec for rec in load_log_records(selected["log_path"]) if rec.get("type") != "summary"]
    if not records:
        st.info("Log file is empty.")
        return
    st.dataframe(records[:200], use_container_width=True)


def _run_tests() -> Dict[str, Any]:
    try:
        completed = subprocess.run(
            ["pytest", "-q"],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - defensive guard for the UI
        return {
            "returncode": -1,
            "message": f"Error running tests: {exc}",
            "output": "",
        }

    output = completed.stdout or ""
    if completed.stderr:
        output = f"{output}\n{completed.stderr}" if output else completed.stderr

    return {
        "returncode": completed.returncode,
        "message": "Tests passed" if completed.returncode == 0 else "Tests failed",
        "output": output.strip(),
    }


def _sidebar_widget(key: str, cfg: Dict[str, Any]) -> Any:
    label = cfg.get("label", key.replace("_", " ").title())
    widget_type = cfg.get("type", "text")

    if widget_type == "select":
        options = cfg.get("options", ())
        default = cfg.get("default")
        index = options.index(default) if default in options else 0
        return st.sidebar.selectbox(label, options, index=index, key=key)

    if widget_type == "number":
        default = cfg.get("default", 0)
        min_val = cfg.get("min", default)
        max_val = cfg.get("max", default)
        step = cfg.get("step", 1)
        return st.sidebar.number_input(label, value=default, min_value=min_val, max_value=max_val, step=step, key=key)

    if widget_type == "slider":
        min_val = cfg.get("min", 0)
        max_val = cfg.get("max", 1000 if isinstance(min_val, int) else 1.0)
        default = cfg.get("default", min_val)
        step = cfg.get("step", 1 if isinstance(min_val, int) else 0.01)
        return st.sidebar.slider(label, min_value=min_val, max_value=max_val, value=default, step=step, key=key)

    if widget_type == "checkbox_group":
        options = cfg.get("options", ())
        return st.sidebar.multiselect(label, options, default=list(options), key=key)

    if widget_type == "toggle":
        default = cfg.get("default", False)
        return st.sidebar.checkbox(label, value=default, key=key)

    if widget_type == "file_uploader":
        accept = cfg.get("accept")
        return st.sidebar.file_uploader(label, type=accept, key=key)

    if widget_type == "button_group":
        buttons = cfg.get("buttons", ())
        return st.sidebar.radio(label, buttons, key=key)

    return st.sidebar.text_input(label, key=key)


def render_sidebar() -> Dict[str, Any]:
    st.sidebar.header("Configuration")
    state: Dict[str, Any] = {}
    for key, cfg in SPEC["controls"].items():
        state[key] = _sidebar_widget(key, cfg)

    if st.sidebar.button("Run tests", type="primary", key="run_tests"):
        with st.sidebar:
            with st.spinner("Running pytest -q..."):
                st.session_state["test_results"] = _run_tests()

    test_result = st.session_state.get("test_results")
    if test_result:
        renderer = st.sidebar.success if test_result.get("returncode") == 0 else st.sidebar.error
        renderer(test_result.get("message", "Test run completed."))
        output = test_result.get("output")
        if output:
            st.sidebar.code(output[-4000:], language="bash")
    return state


def render_main(state: Dict[str, Any]) -> None:
    st.title("Dual-substrate Benchmark Harness")
    st.caption("Interactive shell powered by the declarative Streamlit spec")

    st.subheader("Selections")
    st.json(state)

    all_results = load_results()
    filtered = filter_results(all_results, state.get("model"))

    st.subheader("Run comparison overview")
    if filtered:
        st.dataframe(comparison_table(filtered), use_container_width=True, hide_index=True)
    else:
        st.info("No runs match the current sidebar configuration – upload or generate new results to continue.")

    st.subheader("Retention curve")
    retention = retention_curve_data(filtered)
    if retention:
        st.vega_lite_chart(
            retention,
            {
                "mark": {"type": "line", "point": True},
                "encoding": {
                    "x": {"field": "turns", "type": "quantitative"},
                    "y": {"field": "Recall@1", "type": "quantitative", "scale": {"domain": [0, 1]}},
                    "color": {"field": "model", "type": "nominal"},
                    "tooltip": ["model", "turns", "Recall@1"],
                },
            },
            use_container_width=True,
        )
    else:
        st.info("No retention data available. Run a benchmark first or adjust the filters.")

    st.subheader("Drift timeline")
    drift = drift_timeline_data(filtered)
    if drift:
        st.vega_lite_chart(
            drift,
            {
                "mark": "circle",
                "encoding": {
                    "x": {"field": "turns", "type": "quantitative"},
                    "y": {"field": "contradiction rate", "type": "quantitative", "scale": {"domain": [0, 1]}},
                    "color": {"field": "model", "type": "nominal"},
                    "tooltip": ["model", "turns", "contradiction rate"],
                },
            },
            use_container_width=True,
        )
    else:
        st.info("No drift data available for the selected configuration.")

    st.subheader("Efficiency vs context length")
    efficiency = efficiency_data(filtered)
    if efficiency:
        st.vega_lite_chart(
            efficiency,
            {
                "mark": {"type": "line", "point": True},
                "encoding": {
                    "x": {"field": "turns", "type": "quantitative"},
                    "y": {"field": "value", "type": "quantitative"},
                    "color": {"field": "metric", "type": "nominal"},
                    "strokeDash": {"field": "model", "type": "nominal"},
                    "tooltip": ["model", "metric", "turns", "value"],
                },
            },
            use_container_width=True,
        )
    else:
        st.info("No efficiency data is available yet.")

    st.subheader("Ledger growth")
    ledger = ledger_growth_data(filtered)
    if ledger:
        st.vega_lite_chart(
            ledger,
            {
                "mark": {"type": "line", "point": True},
                "encoding": {
                    "x": {"field": "writes", "type": "quantitative"},
                    "y": {"field": "bit-length(L)", "type": "quantitative"},
                    "color": {"field": "run", "type": "nominal"},
                    "tooltip": ["run", "writes", "bit-length(L)"],
                },
            },
            use_container_width=True,
        )
    else:
        st.info("Ledger activity has not been recorded yet for the selected run(s).")

    _render_throughput_gauge(filtered)

    st.subheader("Probe confusion")
    probes = probe_confusion_data(filtered)
    if probes:
        st.vega_lite_chart(
            probes,
            {
                "mark": "rect",
                "encoding": {
                    "x": {"field": "probe", "type": "ordinal"},
                    "y": {"field": "model", "type": "nominal"},
                    "color": {"field": "rate", "type": "quantitative", "scale": {"domain": [0, 1]}},
                    "tooltip": ["model", "probe", "rate"],
                },
            },
            use_container_width=True,
        )
    else:
        st.info("No probe interactions recorded for the current selection.")

    st.subheader("Entity recall heatmap")
    recall = entity_recall_data(filtered)
    if recall:
        st.vega_lite_chart(
            recall,
            {
                "mark": "rect",
                "encoding": {
                    "x": {"field": "checkpoint", "type": "nominal"},
                    "y": {"field": "entity", "type": "nominal"},
                    "color": {"field": "success", "type": "quantitative", "scale": {"domain": [0, 1]}},
                    "tooltip": ["run", "entity", "checkpoint", "success"],
                },
            },
            use_container_width=True,
        )
    else:
        st.info("No checkpoint evaluations available.")

    st.subheader("Energy bar chart")
    energy = energy_data(filtered)
    if energy:
        st.vega_lite_chart(
            energy,
            {
                "mark": "bar",
                "encoding": {
                    "x": {"field": "model", "type": "nominal"},
                    "y": {"field": "avg energy", "type": "quantitative"},
                    "tooltip": ["model", "avg energy", "tokens"],
                },
            },
            use_container_width=True,
        )
    else:
        st.info("Energy proxies are not available for the selected runs.")

    _render_event_log(filtered)

    st.subheader("Operational Notes")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Interactions**")
        st.json(SPEC["interactions"])
        st.markdown("**Performance**")
        st.json(SPEC["performance"])
    with col2:
        st.markdown("**Data Model**")
        st.json(SPEC["data_model"])
        st.markdown("**Security**")
        st.json(SPEC["security"])

    st.subheader("Wishlist")
    st.json(SPEC["nice_to_have"])


def main() -> None:
    state = render_sidebar()
    render_main(state)


if __name__ == "__main__":
    main()
