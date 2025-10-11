"""Quick-start demo for the dual-substrate harness."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import List

from p_adic_memory.dataset import dialogue_stream, load_items
from p_adic_memory.dual_substrate import DualSubstrate


def main() -> None:
    model = DualSubstrate(dim=128, cycle=900, enable_shuffle=True)
    facts, probes = load_items()
    records = []
    seen_symbols: List[str] = []
    turn_counter = 0
    for event in dialogue_stream(facts, probes, total_turns=1200):
        turn_counter = event["t"]
        if event["role"] == "system":
            symbol = event["id"]
            seen_symbols.append(symbol)
            obs = model.observe(symbol, event.get("truth", 1.0))
            records.append({"turn": event["t"], "type": "write", **obs})
            continue
        if "qid" in event:
            symbol = event["target"]
            expect, flag = model.query(symbol)
            records.append({
                "turn": event["t"],
                "type": "checkpoint",
                "name": event["qid"],
                "symbol": symbol,
                "expect": expect,
                "ledger_flag": flag,
            })
            continue
        if "probe_id" in event:
            symbol = event["probe_id"]
            expect, flag = model.query(symbol)
            records.append({
                "turn": event["t"],
                "type": "probe",
                "name": event["probe_id"],
                "symbol": symbol,
                "expect": expect,
                "ledger_flag": flag,
            })
            continue
        if "truth" in event and seen_symbols:
            symbol = random.choice(seen_symbols)
            obs = model.observe(symbol, event["truth"])
            records.append({"turn": event["t"], "type": "filler", **obs})
    summary = {"type": "summary", "model": "dual_substrate_demo", "tokens": turn_counter + 1}
    summary.update(model.stats())
    records.append(summary)
    out_path = Path("logs/demo.jsonl")
    model.save_log(out_path, records)
    print(json.dumps(model.stats(), indent=2))


if __name__ == "__main__":
    main()
