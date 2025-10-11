"""Benchmark runner for the dual-substrate public release."""

from __future__ import annotations

import argparse
import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from p_adic_memory.baselines import build_baseline
from p_adic_memory.dataset import dialogue_stream, load_items
from p_adic_memory.dual_substrate import DualSubstrate, build_model

random.seed(137)

TRUTH_MAP: Dict[str, Tuple[str, ...]] = {
    "F1": ("self-explanatory", "multivalent"),
    "F2": ("true but unprovable", "godel", "incompleteness"),
    "F5": ("all", "lla", "awareness", "life"),
    "F8": ("metatron", "space", "topology", "wheels", "lawful", "time"),
    "F11": ("space is state", "state transitions", "not empty space"),
}
FALSE_PROBES = {"CP1", "CP2", "CP3", "CP4", "CP5", "CP6"}
CHECKPOINT_MAP = {
    "Q_T0": "F1",
    "Q_GODEL": "F2",
    "Q_WHEELS": "F8",
    "Q_MOVE": "F11",
    "Q_ALL": "F5",
}


def build(name: str, cycle: int, shuffle: bool) -> object:
    if name == "dual_substrate":
        return build_model(name, cycle=cycle, enable_shuffle=shuffle)
    return build_baseline(name)


def run(model_name: str, cycle: int, shuffle: bool, total_turns: int, log_dir: Path) -> Path:
    model = build(model_name, cycle=cycle, shuffle=shuffle)
    facts, probes = load_items()
    seen: List[str] = []
    records: List[Dict[str, object]] = []
    tokens = 0
    recall_events = []
    drift_events = []

    t0 = time.time()
    for event in dialogue_stream(facts, probes, total_turns=total_turns):
        tokens += 1
        if event["role"] == "system":
            symbol = event["id"]
            seen.append(symbol)
            if hasattr(model, "observe"):
                model.observe(symbol, event.get("truth", 1.0))
            records.append({
                "turn": event["t"],
                "type": "write",
                "symbol": symbol,
                "truth": event.get("truth", 1.0),
            })
            continue
        if "probe_id" in event:
            expect, flag = model.query(event["probe_id"])
            success = not flag
            drift_events.append((event["t"], success))
            records.append({
                "turn": event["t"],
                "type": "probe",
                "name": event["probe_id"],
                "probe_id": event["probe_id"],
                "label": event["label"],
                "expect": expect,
                "ledger_flag": flag,
                "success": success,
            })
            continue
        if "qid" in event:
            target = CHECKPOINT_MAP[event["qid"]]
            expect, flag = model.query(target)
            success = bool(flag)
            recall_events.append((event["t"], success))
            records.append({
                "turn": event["t"],
                "type": "checkpoint",
                "name": event["qid"],
                "qid": event["qid"],
                "target": target,
                "expect": expect,
                "ledger_flag": flag,
                "success": success,
            })
            continue
        filler_symbol = random.choice(seen) if seen else None
        if hasattr(model, "observe") and filler_symbol is not None:
            model.observe(filler_symbol, event.get("truth", 0.7))
        records.append({
            "turn": event["t"],
            "type": "filler",
            "symbol": filler_symbol,
            "truth": event.get("truth", 0.7),
        })
    elapsed = time.time() - t0

    recall_rate = sum(s for _, s in recall_events) / max(1, len(recall_events))
    drift_rate = 1.0 - (sum(s for _, s in drift_events) / max(1, len(drift_events)))
    half_life = next((turn for turn, success in recall_events if not success), float("inf"))

    stats = getattr(model, "stats", lambda: {})()
    summary = {
        "model": model_name,
        "tokens": tokens,
        "elapsed_s": elapsed,
        "tokens_per_s": tokens / elapsed if elapsed else float("inf"),
        "recall@1": recall_rate,
        "drift_rate": drift_rate,
        "retention_half_life": half_life,
        "ops_proxy": stats.get("ops"),
        "symbols": stats.get("symbols"),
        "cycle": cycle,
        "shuffle": shuffle,
    }
    records.append({"type": "summary", **summary})

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    log_path = log_dir / f"{model_name}_{timestamp}.jsonl"
    log_dir.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record) + "\n")
    print(json.dumps(summary, indent=2))
    return log_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the dual-substrate benchmark")
    parser.add_argument("--model", choices=[
        "dual_substrate",
        "baseline_transformer",
        "nolima_baseline",
    ], required=True)
    parser.add_argument("--cycle", type=int, default=900, help="Cycle length for the dual substrate")
    parser.add_argument("--no-shuffle", action="store_true", help="Disable Möbius-style shuffle")
    parser.add_argument("--turns", type=int, default=2200, help="Total turns to simulate")
    parser.add_argument("--log-dir", type=Path, default=Path("logs"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args.model, args.cycle, not args.no_shuffle, args.turns, args.log_dir)


if __name__ == "__main__":
    main()
