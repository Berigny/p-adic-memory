"""Command-line entry point for generating Grok memory benchmark reports."""

from __future__ import annotations

import json
import pathlib
import sys
from dataclasses import asdict

from .simulation import HardwareSample, MetricSnapshot, compare_models


def _serialize_snapshots(results: dict[str, list[MetricSnapshot]]) -> dict[str, list[dict[str, float]]]:
    return {model: [asdict(snapshot) for snapshot in snapshots] for model, snapshots in results.items()}


def _serialize_trace(trace: dict[str, list[HardwareSample]]) -> dict[str, list[dict[str, float]]]:
    return {model: [asdict(sample) for sample in samples] for model, samples in trace.items()}


def main() -> None:
    out_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("report.json")
    compare_out = compare_models(capture_trace=True)
    if isinstance(compare_out, tuple):
        results, trace = compare_out
    else:
        results, trace = compare_out, {}

    payload = {
        "snapshots": _serialize_snapshots(results),
        "hardware_trace": _serialize_trace(trace),
    }

    out_path.write_text(json.dumps(payload, indent=2))
    print(f"✅  25-min A/B done → {out_path}")


if __name__ == "__main__":
    main()
