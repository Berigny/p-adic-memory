"""Contract tests for the declarative Streamlit spec."""

from __future__ import annotations

from p_adic_memory.streamlit_spec import get_streamlit_spec


def test_controls_match_product_brief() -> None:
    spec = get_streamlit_spec()
    controls = spec["controls"]

    assert controls["model"]["options"] == ("dual-substrate", "transformer", "NoLiMa")
    assert controls["dataset"]["options"] == ("generic", "uploaded transcript", "saved set")
    assert controls["seed"]["default"] == 137
    assert controls["turns"]["min"] == 500 and controls["turns"]["max"] == 5000
    assert controls["cache_dim"]["min"] == 64 and controls["cache_dim"]["max"] == 512
    assert controls["cycle_length"]["default"] == 900
    assert controls["continuous_cache_lr"]["min"] == 0.001
    assert controls["baselines"]["options"] == ("A", "B", "C")
    assert controls["energy_proxy"]["options"] == ("ops×tokens", "custom coeff")
    assert controls["anonymised_mode"]["default"] is True
    assert controls["upload_transcript"]["accept"] == (".txt", ".md", ".docx")
    assert controls["export"]["buttons"] == ("results.csv", "metrics.json", "logs")


def test_spec_lists_all_required_views_and_sections() -> None:
    spec = get_streamlit_spec()
    charts = spec["charts"]

    expected_chart_keys = {
        "retention_curve",
        "drift_timeline",
        "efficiency",
        "ledger_growth",
        "throughput_gauge",
        "probe_confusion",
        "entity_recall",
        "energy",
        "run_comparison",
        "event_log",
    }

    assert set(charts) == expected_chart_keys
    assert charts["retention_curve"]["y"] == "Recall@1"
    assert charts["drift_timeline"]["markers"] == ("probes", "Möbius events")
    assert charts["efficiency"]["overlays"] == ("O(n^2) band", "~linear")
    assert charts["ledger_growth"]["annotations"][0] == "prime flip #1"
    assert "tokens/sec" in charts["throughput_gauge"]["metrics"]
    assert charts["probe_confusion"]["axes"][0] == "CP1"
    assert charts["entity_recall"]["type"] == "heatmap"
    assert charts["energy"]["error_bars"] is True
    assert "half-life" in charts["run_comparison"]["columns"]
    assert "ledger_flag" in charts["event_log"]["schema"]


def test_spec_describes_interactions_and_guardrails() -> None:
    spec = get_streamlit_spec()

    interactions = spec["interactions"]
    assert interactions["run_controls"] == ("Run", "Pause", "Reset")
    assert "deltas" in interactions["ab_toggle"]["behaviour"]
    assert "Möbius" in interactions["markers"]["hover"][1]
    assert interactions["snapshot"]["behaviour"].startswith("Save run configuration")

    security = spec["security"]
    assert security["anonymised_default"] is True
    assert "Demo harness" in security["export_watermark"]
    assert "private URL" in security["nda_mode"]

    performance = spec["performance"]
    assert performance["incremental_metrics"] is True
    assert performance["cache_dataset"] == "st.cache_data"

    data_model = spec["data_model"]
    assert any(key.endswith("config.json") for key in data_model)
    assert any(key.endswith("metrics.json") for key in data_model)
    assert data_model["results.csv"].startswith("appended per snapshot")

    nice = spec["nice_to_have"]
    assert "parameter_sweep" in nice and "Pareto" in nice["parameter_sweep"]["description"]

