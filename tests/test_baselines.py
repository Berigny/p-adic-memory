"""Tests for baseline reference models."""

from __future__ import annotations

from p_adic_memory.baselines import BaselineTransformer, NoLiMaBaseline


def test_baseline_transformer_decay_and_threshold() -> None:
    model = BaselineTransformer(decay=0.5, threshold=0.4)

    model.observe("Alice", 1.0)
    model.observe("Bob", 0.2)

    value, flag = model.query("Alice")

    assert value == 0.5
    assert flag is True
    assert model.stats()["symbols"] == 2


def test_nolima_baseline_capacity_eviction() -> None:
    model = NoLiMaBaseline(capacity=2, decay=1.0)

    model.observe("A", 1.0)
    model.observe("B", 1.0)
    model.observe("C", 1.0)

    assert model.query("A")[0] == 0.0
    assert "C" in model._weights
    assert model.stats()["symbols"] == 2
