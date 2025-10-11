"""Tests for dataset utilities."""

from __future__ import annotations

from pathlib import Path

from p_adic_memory.dataset import dialogue_stream, load_items


def test_load_items_splits_facts_and_probes() -> None:
    dataset_path = Path(__file__).resolve().parent.parent / "dataset.jsonl"

    facts, probes = load_items(dataset_path)

    assert facts and probes
    assert all(item["type"] == "fact" for item in facts)
    assert all(item["type"] == "probe" for item in probes)


def test_dialogue_stream_emits_expected_events() -> None:
    facts = [{"id": "F1", "text": "Fact text."}]
    probes = [{"id": "P1", "label": "contradiction", "text": "Probe text."}]

    stream = list(dialogue_stream(facts, probes, total_turns=240, seed=7))

    assert stream[0]["role"] == "system"
    assert stream[0]["truth"] == 1.0

    probe_msgs = [item for item in stream if item.get("probe_id")]
    assert len(probe_msgs) == 1
    assert probe_msgs[0]["label"] == "contradiction"

    continuation_msgs = [item for item in stream if item.get("truth") == 0.7]
    assert continuation_msgs
