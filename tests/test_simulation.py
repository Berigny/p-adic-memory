from p_adic_memory.simulation import MetricSnapshot, compare_models


def test_compare_models_shapes():
    results = compare_models(duration_minutes=1, tokens_per_minute=10)
    assert set(results.keys()) == {"Grok + transformers", "Grok + dual substrate"}

    for snapshots in results.values():
        assert snapshots, "expected non-empty snapshots"
        assert all(isinstance(s, MetricSnapshot) for s in snapshots)
        minutes = [s.minute for s in snapshots]
        assert minutes == sorted(minutes), "snapshots should be time-ordered"
