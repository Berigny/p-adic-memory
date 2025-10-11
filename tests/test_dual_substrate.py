"""Tests for the dual substrate harness."""

from __future__ import annotations

import math

from p_adic_memory.dual_substrate import DualSubstrate, PrimeLedger


def test_observe_registers_symbol_and_sets_ledger_flag() -> None:
    brain = DualSubstrate(dim=8, cycle=0, enable_shuffle=False)

    result = brain.observe("Alice", 1.0)

    assert brain.ledger.check("Alice")
    assert math.isfinite(result["expect"])
    assert result["ledger_flag"] is True
    assert len(brain.continuous._projectors) == 1
    assert brain.stats()["symbols"] == 1


def test_multiple_observations_update_stats() -> None:
    brain = DualSubstrate(dim=8, cycle=0, enable_shuffle=False)

    brain.observe("Alice", 1.0)
    result = brain.observe("Alice", 0.0)

    assert math.isfinite(result["expect"])
    assert isinstance(result["ledger_flag"], bool)
    assert brain.stats()["step"] == 2


def test_cycle_shuffle_executes_without_modifying_symbol_order() -> None:
    brain = DualSubstrate(dim=8, cycle=1, enable_shuffle=True)

    brain.observe("Alice", 1.0)
    brain.observe("Bob", 1.0)

    assert brain.ledger.symbols == ["Alice", "Bob"]
    # cycle=1 triggers shuffle on every step; make sure ops counter advanced
    assert brain.continuous.ops > 0


def test_prime_ledger_delete_removes_symbol() -> None:
    ledger = PrimeLedger()

    ledger.write("alice")
    assert ledger.check("alice") is True

    ledger.delete("alice")
    assert ledger.check("alice") is False
    assert ledger.bits >= 0
