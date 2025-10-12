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


@dataclass
class LSTMBaseline:
    """A simple LSTM-based baseline for sequence memory."""

    hidden_size: int = 64
    learning_rate: float = 0.1
    threshold: float = 0.5

    def __post_init__(self):
        # Simplified LSTM components
        self.W_i = {k: random.uniform(-0.1, 0.1) for k in ['xi', 'hi']}
        self.b_i = 0.0
        self.W_f = {k: random.uniform(-0.1, 0.1) for k in ['xf', 'hf']}
        self.b_f = 0.0
        self.W_o = {k: random.uniform(-0.1, 0.1) for k in ['xo', 'ho']}
        self.b_o = 0.0
        self.W_c = {k: random.uniform(-0.1, 0.1) for k in ['xc', 'hc']}
        self.b_c = 0.0

        self.hidden_state = [0.0] * self.hidden_size
        self.cell_state = [0.0] * self.hidden_size

        self._memory: Dict[str, float] = {}
        self._ops: int = 0

    def _sigmoid(self, x: float) -> float:
        self._ops += 1
        return 1 / (1 + math.exp(-x))

    def _tanh(self, x: float) -> float:
        self._ops += 1
        return math.tanh(x)

    def observe(self, symbol: str, truth: float) -> None:
        # One-hot encode the symbol for simplicity
        input_vec = [0.0] * 1  # Simplified input
        input_vec[0] = hash(symbol) % 100 / 100.0 # Simple hash-based input feature

        for i in range(self.hidden_size):
            # LSTM cell calculations
            input_gate = self._sigmoid(self.W_i['xi'] * input_vec[0] + self.W_i['hi'] * self.hidden_state[i] + self.b_i)
            forget_gate = self._sigmoid(self.W_f['xf'] * input_vec[0] + self.W_f['hf'] * self.hidden_state[i] + self.b_f)
            output_gate = self._sigmoid(self.W_o['xo'] * input_vec[0] + self.W_o['ho'] * self.hidden_state[i] + self.b_o)
            cell_candidate = self._tanh(self.W_c['xc'] * input_vec[0] + self.W_c['hc'] * self.hidden_state[i] + self.b_c)

            self.cell_state[i] = (forget_gate * self.cell_state[i]) + (input_gate * cell_candidate)
            self.hidden_state[i] = output_gate * self._tanh(self.cell_state[i])
            self._ops += 10 # Approximate ops for LSTM cell

        # Update memory based on LSTM output and truth
        prediction = self.query(symbol)[0]
        error = truth - prediction

        # Store the "truth" value, potentially adjusted by a learning rule
        self._memory[symbol] = self._memory.get(symbol, 0.0) + self.learning_rate * error
        self._ops += 2

    def query(self, symbol: str) -> Tuple[float, bool]:
        # A simple query: does the symbol exist in memory with a value above threshold?
        value = self._memory.get(symbol, 0.0)
        return value, value >= self.threshold

    def stats(self) -> Dict[str, float]:
        return {"ops": float(self._ops), "symbols": len(self._memory)}


MODEL_BUILDERS = {
    "baseline_transformer": BaselineTransformer,
    "nolima_baseline": NoLiMaBaseline,
    "lstm_baseline": LSTMBaseline,
}


def build_baseline(name: str, **kwargs):
    if name not in MODEL_BUILDERS:
        raise ValueError(f"Unknown baseline '{name}'")
    return MODEL_BUILDERS[name](**kwargs)
