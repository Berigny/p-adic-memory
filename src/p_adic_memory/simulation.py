"""Simulation utilities for comparing transformer and dual-substrate memories."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# Prime utilities and append-only ledger
# ---------------------------------------------------------------------------

def _prime_generator(limit: int = 100_000) -> List[int]:
    """Generate a list of primes up to ``limit`` using a simple sieve."""

    sieve = [True] * (limit + 1)
    sieve[0:2] = [False, False]
    for p in range(2, int(limit**0.5) + 1):
        if sieve[p]:
            step = p
            start = p * p
            sieve[start : limit + 1 : step] = [False] * ((limit - start) // step + 1)
    return [i for i, is_prime in enumerate(sieve) if is_prime]


_SMALL_PRIMES: Sequence[int] = _prime_generator()


class PrimeLedger:
    """Append-only ledger that maps symbols to unique primes."""

    def __init__(self) -> None:
        self._supply: Iterator[int] = iter(_SMALL_PRIMES)
        self._value: int = 1
        self._map: Dict[str, int] = {}

    @staticmethod
    def _valuation(n: int, p: int) -> int:
        if n == 0:
            return 999
        k = 0
        while n % p == 0:
            n //= p
            k += 1
        return k

    def register(self, symbol: str) -> int:
        if symbol not in self._map:
            self._map[symbol] = next(self._supply)
        return self._map[symbol]

    def write(self, symbol: str) -> None:
        prime = self.register(symbol)
        self._value *= prime

    def check(self, symbol: str) -> bool:
        prime = self._map.get(symbol)
        if prime is None:
            return False
        return self._valuation(self._value, prime) > 0

    @property
    def size(self) -> int:
        return len(self._map)


# ---------------------------------------------------------------------------
# Continuous cache used by both memories
# ---------------------------------------------------------------------------


class ContinuousCache:
    def __init__(self, dim: int = 128) -> None:
        self.dim = dim
        self.x: List[float] = [0.0] * dim
        self.projectors: List[List[List[float]]] = []

    @staticmethod
    def _random_unit_vector(dim: int) -> List[float]:
        values = [random.gauss(0, 1) for _ in range(dim)]
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

    def add_projector(self) -> None:
        v = self._random_unit_vector(self.dim)
        projector = [[v[i] * v[j] for j in range(self.dim)] for i in range(self.dim)]
        self.projectors.append(projector)

    def expect(self, idx: int) -> float:
        projector = self.projectors[idx]
        total = 0.0
        x = self.x
        for j in range(self.dim):
            row = projector[j]
            for k in range(self.dim):
                total += x[j] * row[k] * x[k]
        return total

    def gradient_step(self, idx: int, target: float, lr: float = 0.05) -> None:
        projector = self.projectors[idx]
        prediction = self.expect(idx)
        error = target - prediction
        grad: List[float] = [0.0] * self.dim
        x = self.x
        for j in range(self.dim):
            row = projector[j]
            grad[j] = 2.0 * sum(row[k] * x[k] for k in range(self.dim))
        for j in range(self.dim):
            x[j] += lr * error * grad[j]

    def energy(self) -> float:
        return sum(value * value for value in self.x)


# ---------------------------------------------------------------------------
# Memory substrates
# ---------------------------------------------------------------------------


class TransformerMemory:
    def __init__(self, dim: int = 128) -> None:
        self.cache = ContinuousCache(dim)
        self.symbol_to_index: Dict[str, int] = {}

    def observe(self, symbol: str, truth: float) -> None:
        idx = self.symbol_to_index.get(symbol)
        if idx is None:
            idx = len(self.symbol_to_index)
            self.symbol_to_index[symbol] = idx
            self.cache.add_projector()
        self.cache.gradient_step(idx, truth)

    def query(self, symbol: str) -> float:
        idx = self.symbol_to_index.get(symbol)
        if idx is None:
            return 0.0
        return self.cache.expect(idx)

    def energy(self) -> float:
        return self.cache.energy()


class DualSubstrateMemory:
    def __init__(self, dim: int = 128, cycle_minutes: float = 15.0) -> None:
        self.continuous = ContinuousCache(dim)
        self.discrete = PrimeLedger()
        self.symbol_to_index: Dict[str, int] = {}
        self.cycle_minutes = cycle_minutes
        self.cycle_steps = 0
        self.step = 0

    def observe(self, symbol: str, truth: float) -> None:
        idx = self.symbol_to_index.get(symbol)
        if idx is None:
            idx = len(self.symbol_to_index)
            self.symbol_to_index[symbol] = idx
            self.discrete.register(symbol)
            self.continuous.add_projector()
        self.continuous.gradient_step(idx, truth)
        if truth >= 0.5:
            self.discrete.write(symbol)
        self.step += 1
        if self.cycle_steps and self.step % self.cycle_steps == 0:
            perm = list(range(self.continuous.dim))
            random.shuffle(perm)
            self.continuous.x = [self.continuous.x[perm[i]] for i in range(self.continuous.dim)]

    def query(self, symbol: str) -> Tuple[float, bool]:
        idx = self.symbol_to_index.get(symbol)
        if idx is None:
            return 0.0, False
        return self.continuous.expect(idx), self.discrete.check(symbol)

    def energy(self) -> float:
        continuous_energy = self.continuous.energy()
        size = self.discrete.size
        discrete_penalty = math.log(size + 1) / 1000.0 if size else 0.0
        return continuous_energy + discrete_penalty


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------


@dataclass
class MetricSnapshot:
    minute: float
    recall: float
    drift: float
    energy: float


def _symbol_sequence(seed: int, population: Sequence[str], steps: int) -> Iterable[str]:
    rng = random.Random(seed)
    for _ in range(steps):
        yield rng.choice(population)


def simulate_memory(
    memory: TransformerMemory | DualSubstrateMemory,
    *,
    duration_minutes: int = 25,
    tokens_per_minute: int = 60,
    recall_threshold: float = 0.5,
) -> List[MetricSnapshot]:
    steps = duration_minutes * tokens_per_minute
    names = ["Alice", "Bob", "Charlie", "Delta", "Echo"] * 17
    seen: Dict[str, int] = {}
    snapshots: List[MetricSnapshot] = []

    if isinstance(memory, DualSubstrateMemory):
        memory.cycle_steps = int(memory.cycle_minutes * tokens_per_minute) if memory.cycle_minutes else 0

    for t, symbol in enumerate(_symbol_sequence(42, names, steps), start=1):
        count = seen.get(symbol, 0)
        truth = 1.0 if count == 0 else 0.7
        seen[symbol] = count + 1

        memory.observe(symbol, truth)

        if isinstance(memory, DualSubstrateMemory):
            expected, _ = memory.query(symbol)
        else:
            expected = memory.query(symbol)

        recall_flag = 1.0 if expected >= recall_threshold else 0.0

        drift = abs(expected - truth)
        energy = memory.energy()
        minute = t / tokens_per_minute
        snapshots.append(MetricSnapshot(minute=minute, recall=recall_flag, drift=drift, energy=energy))

    return snapshots


def compare_models(
    *,
    duration_minutes: int = 25,
    tokens_per_minute: int = 60,
    dim: int = 128,
    cycle_minutes: float = 15.0,
) -> Dict[str, List[MetricSnapshot]]:
    random.seed(1234)
    transformer = TransformerMemory(dim=dim)
    dual = DualSubstrateMemory(dim=dim, cycle_minutes=cycle_minutes)

    return {
        "Grok + transformers": simulate_memory(
            transformer,
            duration_minutes=duration_minutes,
            tokens_per_minute=tokens_per_minute,
        ),
        "Grok + dual substrate": simulate_memory(
            dual,
            duration_minutes=duration_minutes,
            tokens_per_minute=tokens_per_minute,
        ),
    }
