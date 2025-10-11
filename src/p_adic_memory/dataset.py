"""Benchmark dataset and dialogue stream helpers."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Tuple

random.seed(137)


def load_items(path: str | Path = "dataset.jsonl") -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        items = [json.loads(line) for line in fh]
    facts = [item for item in items if item["type"] == "fact"]
    probes = [item for item in items if item["type"] == "probe"]
    return facts, probes


def dialogue_stream(
    facts: List[Dict[str, str]],
    probes: List[Dict[str, str]],
    total_turns: int = 2200,
    seed: int = 137,
) -> Iterator[Dict[str, object]]:
    random.seed(seed)
    fact_indices = list(range(len(facts)))
    random.shuffle(fact_indices)
    fact_ptr = 0
    for turn in range(total_turns):
        if turn % 50 == 0 and fact_ptr < len(fact_indices):
            fact = facts[fact_indices[fact_ptr]]
            fact_ptr += 1
            yield {
                "t": turn,
                "role": "system",
                "id": fact["id"],
                "content": fact["text"],
                "truth": 1.0,
            }
        if turn in (300, 900, 1500, 2100):
            yield {
                "t": turn,
                "role": "user",
                "qid": "Q_T0",
                "target": "F1",
                "content": "Define T0 in one sentence. Does it permit paradox?",
            }
            yield {
                "t": turn,
                "role": "user",
                "qid": "Q_WHEELS",
                "target": "F8",
                "content": "Metatron’s cube vs Ezekiel’s wheels in one line.",
            }
            yield {
                "t": turn,
                "role": "user",
                "qid": "Q_MOVE",
                "target": "F11",
                "content": "Is movement objects crossing empty space? yes/no, 10 words.",
            }
            yield {
                "t": turn,
                "role": "user",
                "qid": "Q_ALL",
                "target": "F5",
                "content": "Are ALL and LLA identical? yes/no; one-line reason.",
            }
            yield {
                "t": turn,
                "role": "user",
                "qid": "Q_GODEL",
                "target": "F2",
                "content": "State why Gödel matters here in ≤20 words.",
            }
        if turn % 230 == 115 and probes:
            probe = random.choice(probes)
            yield {
                "t": turn,
                "role": "user",
                "probe_id": probe["id"],
                "label": probe["label"],
                "content": probe["text"],
            }
        yield {
            "t": turn,
            "role": "user",
            "content": "Continue the discussion briefly.",
            "truth": 0.7,
        }
