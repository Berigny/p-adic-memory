"""Baseline reference models used in the benchmark suite."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, Tuple

random.seed(137)


@dataclass
class BaselineTransformer:
    """A toy transformer-style baseline with exponential decay."""

    decay: float = 0.995
    threshold: float = 0.5
    _weights: Dict[str, float] = field(default_factory=dict)
    _ops: int = 0

    def observe(self, symbol: str, truth: float) -> None:
        for key in list(self._weights):
            self._weights[key] *= self.decay
            self._ops += 1
        self._weights[symbol] = max(truth, self._weights.get(symbol, 0.0))
        self._ops += 1

    def query(self, symbol: str) -> Tuple[float, bool]:
        value = self._weights.get(symbol, 0.0)
        return value, value >= self.threshold

    def stats(self) -> Dict[str, float]:
        return {"ops": float(self._ops), "symbols": len(self._weights)}


@dataclass
class NoLiMaBaseline:
    """Fixed-capacity vector store inspired by NoLiMa-style memory."""

    capacity: int = 64
    threshold: float = 0.5
    decay: float = 0.99
    _weights: Dict[str, float] = field(default_factory=dict)
    _recency: Dict[str, int] = field(default_factory=dict)
    _step: int = 0
    _ops: int = 0

    def observe(self, symbol: str, truth: float) -> None:
        self._step += 1
        for key in list(self._weights):
            self._weights[key] *= self.decay
            self._ops += 1
        if symbol not in self._weights and len(self._weights) >= self.capacity:
            lru = min(self._recency, key=self._recency.get)
            self._weights.pop(lru, None)
            self._recency.pop(lru, None)
        self._weights[symbol] = max(truth, self._weights.get(symbol, 0.0))
        self._recency[symbol] = self._step
        self._ops += 1

    def query(self, symbol: str) -> Tuple[float, bool]:
        value = self._weights.get(symbol, 0.0)
        return value, value >= self.threshold

    def stats(self) -> Dict[str, float]:
        return {
            "ops": float(self._ops),
            "symbols": len(self._weights),
        }


MODEL_BUILDERS = {
    "baseline_transformer": BaselineTransformer,
    "nolima_baseline": NoLiMaBaseline,
}


def build_baseline(name: str, **kwargs):
    if name not in MODEL_BUILDERS:
        raise ValueError(f"Unknown baseline '{name}'")
    return MODEL_BUILDERS[name](**kwargs)
