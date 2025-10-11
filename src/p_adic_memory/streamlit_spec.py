"""Declarative Streamlit spec for the interactive benchmark harness.

The real Streamlit application that ships with the dual-substrate release is
intentionally thin – the repo purposely avoids shipping Streamlit in the
runtime dependencies.  The tests, however, still need an authoritative
description of the interactive layers so that downstream integrations can be
validated without booting Streamlit itself.

This module therefore exposes :func:`get_streamlit_spec` which returns a
read-only nested structure describing the sidebar controls, main charts, layout
rules, interactions, storage model, and guard-rails documented in the product
brief.  The structure mirrors the human readable spec shared with evaluation
partners and can easily be consumed by tests or by a thin Streamlit front-end
that renders widgets dynamically.

The structure is deliberately comprised of ``Mapping``/``Sequence`` objects so
that callers can serialise it to JSON for schema validation or golden-file
comparisons.  The values are kept lightweight (strings, tuples, ints, floats)
to avoid introducing heavy dependencies into the test environment.
"""

from __future__ import annotations

from typing import Any, Dict


def _controls() -> Dict[str, Any]:
    """Return the sidebar control definition block."""

    return {
        "model": {
            "type": "select",
            "label": "Model",
            "options": ("dual-substrate", "transformer", "NoLiMa"),
        },
        "dataset": {
            "type": "select",
            "label": "Dataset",
            "options": ("generic", "uploaded transcript", "saved set"),
        },
        "seed": {
            "type": "number",
            "label": "Seed",
            "default": 137,
            "value_type": "int",
        },
        "turns": {
            "type": "slider",
            "label": "Turns",
            "min": 500,
            "max": 5000,
            "step": 10,
        },
        "seeding_cadence": {
            "type": "slider",
            "label": "Seeding cadence",
            "description": "Facts injected every N turns",
        },
        "probe_frequency": {
            "type": "slider",
            "label": "Probe frequency",
            "description": "Probe every N turns",
        },
        "cache_dim": {
            "type": "slider",
            "label": "Cache dim (dual-substrate)",
            "min": 64,
            "max": 512,
            "default": 128,
        },
        "cycle_length": {
            "type": "slider",
            "label": "Cycle length (Möbius)",
            "min": 0,
            "max": 2000,
            "default": 900,
            "options": ("off",),
        },
        "continuous_cache_lr": {
            "type": "slider",
            "label": "LR (continuous cache)",
            "min": 0.001,
            "max": 0.2,
            "step": 0.001,
        },
        "baselines": {
            "type": "checkbox_group",
            "label": "Baselines",
            "options": ("A", "B", "C"),
        },
        "energy_proxy": {
            "type": "select",
            "label": "Energy proxy",
            "options": ("ops×tokens", "custom coeff"),
        },
        "anonymised_mode": {
            "type": "toggle",
            "label": "Anonymised mode",
            "default": True,
        },
        "upload_transcript": {
            "type": "file_uploader",
            "label": "Upload transcript",
            "accept": (".txt", ".md", ".docx"),
        },
        "export": {
            "type": "button_group",
            "label": "Export",
            "buttons": ("results.csv", "metrics.json", "logs"),
        },
    }


def _charts() -> Dict[str, Any]:
    """Return the definition for the main visualisations."""

    return {
        "retention_curve": {
            "title": "Retention curve",
            "type": "line",
            "x": "turns",
            "y": "Recall@1",
            "group": "system",
            "notes": "Shows memory half-life; dual-substrate should flatten",
        },
        "drift_timeline": {
            "title": "Drift timeline",
            "type": "scatter",
            "y": "contradiction rate",
            "markers": ("probes", "Möbius events"),
        },
        "efficiency": {
            "title": "Efficiency vs context length",
            "type": "line",
            "y": ("ops proxy", "time/token"),
            "x": "turns",
            "overlays": ("O(n^2) band", "~linear"),
        },
        "ledger_growth": {
            "title": "Ledger growth",
            "type": "log_line",
            "y": "bit-length(L)",
            "x": "writes",
            "annotations": tuple(f"prime flip #{idx}" for idx in range(1, 10)),
            "condition": "dual-substrate",
        },
        "throughput_gauge": {
            "title": "Throughput gauge",
            "type": "kpi",
            "metrics": ("tokens/sec", "turns/sec", "wall-clock"),
        },
        "probe_confusion": {
            "title": "Probe confusion",
            "type": "heatmap",
            "axes": ("CP1", "CP2", "CP3", "CP4", "CP5", "CP6"),
        },
        "entity_recall": {
            "title": "Entity recall heatmap",
            "type": "heatmap",
            "y": "entities",
            "x": "checkpoints",
        },
        "energy": {
            "title": "Energy bar chart",
            "type": "bar",
            "y": "avg energy",
            "error_bars": True,
        },
        "run_comparison": {
            "title": "Run comparison table",
            "type": "table",
            "columns": (
                "system",
                "recall@1",
                "drift%",
                "half-life",
                "ops",
                "tokens/s",
                "energy",
            ),
        },
        "event_log": {
            "title": "Event log viewer",
            "type": "paginated",
            "schema": ("t", "qid", "probe", "answer", "score", "expect", "ledger_flag"),
        },
    }


def _layout() -> Dict[str, Any]:
    """Return the dashboard layout guidelines."""

    return {
        "top_row": ("Recall@1 final", "Drift%", "Half-life", "Energy"),
        "left_column": ("retention_curve", "drift_timeline", "efficiency"),
        "right_column": ("ledger_growth", "energy", "probe_confusion"),
        "bottom": ("entity_recall", "event_log", "export"),
    }


def _interactions() -> Dict[str, Any]:
    """Describe interactive behaviours shared across widgets."""

    return {
        "run_controls": ("Run", "Pause", "Reset"),
        "ab_toggle": {
            "label": "A/B toggle",
            "behaviour": "Highlight reference system and show deltas",
        },
        "markers": {
            "hover": ("probe text", "Möbius flip number"),
        },
        "snapshot": {
            "label": "Snapshot",
            "behaviour": "Save run configuration and metrics for later comparison",
        },
    }


def _data_model() -> Dict[str, Any]:
    """Document the persisted artefacts produced by a run."""

    return {
        "runs/{timestamp}/config.json": "all params (seed, turns, dims, etc.)",
        "runs/{timestamp}/logs.jsonl": "per-turn outputs and probe checks",
        "runs/{timestamp}/metrics.json": "summary metrics",
        "results.csv": "appended per snapshot for quick comparisons",
    }


def _performance() -> Dict[str, Any]:
    """Describe performance guidelines for constrained environments."""

    return {
        "downsampling": "show every kth point to keep charts light",
        "incremental_metrics": True,
        "cache_dataset": "st.cache_data",
        "tiny_transformer": True,
    }


def _security() -> Dict[str, Any]:
    """Capture IP guardrails exposed via the UI."""

    return {
        "anonymised_default": True,
        "hide_update_rules": True,
        "export_watermark": "Demo harness – core IP withheld",
        "nda_mode": "unlock extra traces on private URL",
    }


def _nice_to_have() -> Dict[str, Any]:
    """Optional features tracked for completeness."""

    return {
        "parameter_sweep": {
            "description": "Grid over cycle, dim, LR with Pareto frontier",
        },
        "report_builder": "Generate PDF with top charts and metrics",
        "webhook": "Post nightly run deltas to Codex/MCP/Slack/email",
    }


def get_streamlit_spec() -> Dict[str, Any]:
    """Return the structured Streamlit specification used by tests.

    The returned dictionary is organised into semantic sections to keep unit
    tests resilient to cosmetic changes in any eventual Streamlit front-end.
    """

    return {
        "controls": _controls(),
        "charts": _charts(),
        "layout": _layout(),
        "interactions": _interactions(),
        "data_model": _data_model(),
        "performance": _performance(),
        "security": _security(),
        "nice_to_have": _nice_to_have(),
    }


__all__ = ["get_streamlit_spec"]

