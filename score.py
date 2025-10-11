"""Aggregate benchmark logs into CSV metrics."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List


def parse_log(path: Path) -> Dict[str, object]:
    checkpoints: List[Dict[str, object]] = []
    probes: List[Dict[str, object]] = []
    summary: Dict[str, object] | None = None
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            record = json.loads(line)
            if record.get("type") == "checkpoint":
                checkpoints.append(record)
            elif record.get("type") == "probe":
                probes.append(record)
            elif record.get("type") == "summary":
                summary = record
    if summary is None:
        summary = {}
    if checkpoints:
        summary["recall@1"] = sum(1 for item in checkpoints if item.get("success")) / len(checkpoints)
        summary["retention_half_life"] = next(
            (item["turn"] for item in checkpoints if not item.get("success")),
            float("inf"),
        )
    if probes:
        summary["drift_rate"] = 1.0 - (sum(1 for item in probes if item.get("success")) / len(probes))
    summary["log_path"] = str(path)
    return summary


def write_csv(rows: Iterable[Dict[str, object]], out_file) -> None:
    rows = list(rows)
    if not rows:
        return
    fieldnames = sorted({key for row in rows for key in row.keys()})
    writer = csv.DictWriter(out_file, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score benchmark logs")
    parser.add_argument("paths", nargs="+", type=Path)
    return parser.parse_args()


def main() -> None:
    import sys

    args = parse_args()
    rows = [parse_log(path) for path in args.paths]
    write_csv(rows, sys.stdout)


if __name__ == "__main__":
    main()
