"""Dual-substrate (continuous + discrete) reference implementation.

This module exposes a deterministic harness for the anonymised
ℝ × ℚₚ memory substrate used in the public benchmark.  It implements:

* A continuous cache backed by fixed-rank projectors in a 128-D space.
* An append-only prime ledger with a fixed internal prime pool.
* Optional Möbius-style shuffling of the continuous state every *cycle*
  steps (disabled via flag for ablation studies).
* Deterministic seeds for reproducibility across runs.

The implementation intentionally withholds any proprietary update or
automorphism schedules.  Projector sampling is Gaussian but seeded, and
prime assignment draws from an internal table that is not exported.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

# ----- deterministic seeding -------------------------------------------------
random.seed(137)

# ----- internal prime pool ---------------------------------------------------
# The pool is deliberately small (first 512 primes) and kept private to avoid
# revealing any production schedules.
_PRIME_POOL: Tuple[int, ...] = (
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53,
    59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113,
    127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181,
    191, 193, 197, 199, 211, 223, 227, 229, 233, 239, 241, 251,
    257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317,
    331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389, 397,
    401, 409, 419, 421, 431, 433, 439, 443, 449, 457, 461, 463,
    467, 479, 487, 491, 499, 503, 509, 521, 523, 541, 547, 557,
    563, 569, 571, 577, 587, 593, 599, 601, 607, 613, 617, 619,
    631, 641, 643, 647, 653, 659, 661, 673, 677, 683, 691, 701,
    709, 719, 727, 733, 739, 743, 751, 757, 761, 769, 773, 787,
    797, 809, 811, 821, 823, 827, 829, 839, 853, 857, 859, 863,
    877, 881, 883, 887, 907, 911, 919, 929, 937, 941, 947, 953,
    967, 971, 977, 983, 991, 997, 1009, 1013, 1019, 1021, 1031,
    1033, 1039, 1049, 1051, 1061, 1063, 1069, 1087, 1091, 1093,
    1097, 1103, 1109, 1117, 1123, 1129, 1151, 1153, 1163, 1171,
    1181, 1187, 1193, 1201, 1213, 1217, 1223, 1229, 1231, 1237,
    1249, 1259, 1277, 1279, 1283, 1289, 1291, 1297, 1301, 1303,
    1307, 1319, 1321, 1327, 1361, 1367, 1373, 1381, 1399, 1409,
    1423, 1427, 1429, 1433, 1439, 1447, 1451, 1453, 1459, 1471,
    1481, 1483, 1487, 1489, 1493, 1499, 1511, 1523, 1531, 1543,
    1549, 1553, 1559, 1567, 1571, 1579, 1583, 1597, 1601, 1607,
    1609, 1613, 1619, 1621, 1627, 1637, 1657, 1663, 1667, 1669,
    1693, 1697, 1699, 1709, 1721, 1723, 1733, 1741, 1747, 1753,
    1759, 1777, 1783, 1787, 1789, 1801, 1811, 1823, 1831, 1847,
    1861, 1867, 1871, 1873, 1877, 1879, 1889, 1901, 1907, 1913,
    1931, 1933, 1949, 1951, 1973, 1979, 1987, 1993, 1997, 1999,
    2003, 2011, 2017, 2027, 2029, 2039, 2053, 2063, 2069, 2081,
    2083, 2087, 2089, 2099, 2111, 2113, 2129, 2131, 2137, 2141,
    2143, 2153, 2161, 2179, 2203, 2207, 2213, 2221, 2237, 2239,
    2243, 2251, 2267, 2269, 2273, 2281, 2287, 2293, 2297, 2309,
    2311, 2333, 2339, 2341, 2347, 2351, 2357, 2371, 2377, 2381,
    2383, 2389, 2393, 2399, 2411, 2417, 2423, 2437, 2441, 2447,
    2459, 2467, 2473, 2477, 2503, 2521, 2531, 2539, 2543, 2549,
    2551, 2557, 2579, 2591, 2593, 2609, 2617, 2621, 2633, 2647,
    2657, 2659, 2663, 2671, 2677, 2683, 2687, 2689, 2693, 2699,
    2707, 2711, 2713, 2719, 2729, 2731, 2741, 2749, 2753, 2767,
    2777, 2789, 2791, 2797, 2801, 2803, 2819, 2833, 2837, 2843,
    2851, 2857, 2861, 2879, 2887, 2897, 2903, 2909, 2917, 2927,
    2939, 2953, 2957, 2963, 2969, 2971, 2999, 3001, 3011, 3019,
    3023, 3037, 3041, 3049, 3061, 3067, 3079, 3083, 3089, 3109,
    3119, 3121, 3137, 3163, 3167, 3169, 3181, 3187, 3191, 3203,
    3209, 3217, 3221, 3229, 3251, 3253, 3257, 3259, 3271, 3299,
    3301, 3307, 3313, 3319, 3323, 3329, 3331, 3343, 3347, 3359,
    3361, 3371, 3373, 3389, 3391, 3407, 3413, 3433, 3449, 3457,
    3461, 3463, 3467, 3469, 3491, 3499, 3511, 3517, 3527, 3529,
    3533, 3539, 3541, 3547, 3557, 3559, 3571, 3581, 3583, 3593,
    3607, 3613, 3617, 3623, 3631, 3637, 3643, 3659, 3671, 3673,
    3677, 3691, 3697, 3701, 3709, 3719, 3727, 3733, 3739, 3761,
    3767, 3769, 3779, 3793, 3797, 3803, 3821, 3823, 3833, 3847,
    3851, 3853, 3863, 3877, 3881, 3889, 3907, 3911, 3917, 3919,
    3923, 3929, 3931, 3943, 3947, 3967, 3989, 4001, 4003, 4007,
    4013, 4019, 4021, 4027, 4049, 4051, 4057, 4073, 4079, 4091,
    4093, 4099, 4111, 4127, 4129, 4133, 4139, 4153, 4157, 4159,
    4177, 4201, 4211, 4217, 4219, 4229, 4231, 4241, 4243, 4253,
    4259, 4261, 4271, 4273, 4283, 4289, 4297, 4327, 4337, 4339,
    4349, 4357, 4363, 4373, 4391, 4397, 4409, 4421, 4423, 4441,
    4447, 4451, 4457, 4463, 4481, 4483, 4493, 4507, 4513, 4517,
    4519, 4523, 4547, 4549, 4561, 4567, 4583, 4591, 4597, 4603,
    4621, 4637, 4639, 4643, 4649, 4651, 4657, 4663, 4673, 4679,
    4691, 4703, 4721, 4723, 4729, 4733, 4751, 4759, 4783, 4787,
    4789, 4793, 4799, 4801, 4813, 4817, 4831, 4861, 4871, 4877,
    4889, 4903, 4909, 4919, 4931, 4933, 4937, 4943, 4951, 4957,
    4967, 4969, 4973, 4987, 4993, 4999, 5003, 5009, 5011, 5021,
)


@dataclass
class PrimeLedger:
    """Append-only prime ledger."""

    _assignments: Dict[str, int] = field(default_factory=dict)
    _order: List[str] = field(default_factory=list)
    _product: int = 1
    _next_idx: int = 0

    def register(self, symbol: str) -> int:
        if symbol not in self._assignments:
            if self._next_idx >= len(_PRIME_POOL):
                raise RuntimeError("Prime pool exhausted in public harness")
            self._assignments[symbol] = _PRIME_POOL[self._next_idx]
            self._order.append(symbol)
            self._next_idx += 1
        return self._assignments[symbol]

    def write(self, symbol: str) -> None:
        prime = self.register(symbol)
        self._product *= prime

    def delete(self, symbol: str) -> None:
        prime = self._assignments.get(symbol)
        if prime is None:
            return
        while self._product % prime == 0:
            self._product //= prime

    def check(self, symbol: str) -> bool:
        prime = self._assignments.get(symbol)
        if prime is None:
            return False
        return self._product % prime == 0

    def index(self, symbol: str) -> int:
        return self._order.index(symbol)

    @property
    def symbols(self) -> List[str]:
        return list(self._order)

    @property
    def bits(self) -> int:
        return self._product.bit_length()


@dataclass
class ContinuousCache:
    dim: int = 128
    learning_rate: float = 0.05
    _projectors: List[List[List[float]]] = field(default_factory=list)
    _ops: int = 0

    def __post_init__(self) -> None:
        self._state: List[float] = [0.0] * self.dim

    def add_projector(self) -> None:
        vec = [random.gauss(0.0, 1.0) for _ in range(self.dim)]
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        vec = [v / norm for v in vec]
        projector = [[vec[i] * vec[j] for j in range(self.dim)] for i in range(self.dim)]
        self._projectors.append(projector)

    def expect(self, idx: int) -> float:
        projector = self._projectors[idx]
        total = 0.0
        for j in range(self.dim):
            row_acc = 0.0
            xj = self._state[j]
            for k in range(self.dim):
                row_acc += projector[j][k] * self._state[k]
            total += xj * row_acc
        self._ops += 2 * (self.dim ** 2)
        return total

    def gradient_step(self, idx: int, target: float) -> None:
        projector = self._projectors[idx]
        current = self.expect(idx)
        err = target - current
        grad = [0.0] * self.dim
        for j in range(self.dim):
            row_acc = 0.0
            for k in range(self.dim):
                row_acc += projector[j][k] * self._state[k]
            grad[j] = 2.0 * row_acc
        for j in range(self.dim):
            self._state[j] += self.learning_rate * err * grad[j]
        self._ops += 2 * (self.dim ** 2)

    def shuffle(self, permutation: List[int]) -> None:
        self._state = [self._state[i] for i in permutation]
        shuffled_projectors: List[List[List[float]]] = []
        for proj in self._projectors:
            shuffled = [[proj[i][j] for j in permutation] for i in permutation]
            shuffled_projectors.append(shuffled)
        self._projectors = shuffled_projectors
        self._ops += len(self._projectors) * (self.dim ** 2)

    @property
    def ops(self) -> int:
        return self._ops

    def snapshot(self) -> Dict[str, object]:
        return {
            "dim": self.dim,
            "ops": self._ops,
            "projectors": len(self._projectors),
        }


@dataclass
class DualSubstrate:
    dim: int = 128
    cycle: int = 900
    enable_shuffle: bool = True
    learning_rate: float = 0.05

    continuous: ContinuousCache = field(init=False)
    ledger: PrimeLedger = field(init=False)
    step: int = 0

    def __post_init__(self) -> None:
        self.continuous = ContinuousCache(dim=self.dim, learning_rate=self.learning_rate)
        self.ledger = PrimeLedger()

    def observe(self, symbol: str, truth: float) -> Dict[str, object]:
        if symbol not in self.ledger._assignments:
            self.continuous.add_projector()
            self.ledger.register(symbol)
        idx = self.ledger.index(symbol)
        self.continuous.gradient_step(idx, truth)
        if truth >= 0.5:
            self.ledger.write(symbol)
        else:
            self.ledger.delete(symbol)
        self.step += 1
        if self.enable_shuffle and self.cycle > 0 and self.step % self.cycle == 0:
            perm = list(range(self.dim))
            random.shuffle(perm)
            self.continuous.shuffle(perm)
        expect, ledger_flag = self.query(symbol)
        return {
            "step": self.step,
            "symbol": symbol,
            "expect": expect,
            "ledger_flag": ledger_flag,
            "ops": self.continuous.ops,
        }

    def query(self, symbol: str) -> Tuple[float, bool]:
        if symbol not in self.ledger._assignments:
            return 0.0, False
        idx = self.ledger.index(symbol)
        return self.continuous.expect(idx), self.ledger.check(symbol)

    def stats(self) -> Dict[str, object]:
        return {
            "symbols": len(self.ledger.symbols),
            "ledger_bits": self.ledger.bits,
            "continuous_dim": self.continuous.dim,
            "step": self.step,
            "ops": self.continuous.ops,
        }

    def save_log(self, path: Path, records: Iterable[Dict[str, object]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record) + "\n")


# Convenience factory for CLI usage ------------------------------------------------
MODEL_REGISTRY = {
    "dual_substrate": DualSubstrate,
}


def available_models() -> List[str]:
    return sorted(MODEL_REGISTRY)


def build_model(name: str, **kwargs) -> DualSubstrate:
    if name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model '{name}'")
    return MODEL_REGISTRY[name](**kwargs)
