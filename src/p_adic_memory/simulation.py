# ---------------------------------------------------------------------------
# 1.  Prime pool + crash-safe ledger (up to 664 k symbols)
# ---------------------------------------------------------------------------
import pathlib, pickle, math, random
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple, Iterator

PRIME_CACHE = pathlib.Path(__file__).with_suffix(".primes")

def _load_primes() -> List[int]:
    if PRIME_CACHE.exists():
        return pickle.loads(PRIME_CACHE.read_bytes())
    limit = 10_000_000                                   # 664 579 primes
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for p in range(2, int(limit ** 0.5) + 1):
        if sieve[p]:
            start, step = p * p, p
            sieve[start :: step] = b"\x00" * ((limit - start) // step + 1)
    primes = [i for i, is_p in enumerate(sieve) if is_p]
    PRIME_CACHE.write_bytes(pickle.dumps(primes))
    return primes

_SMALL_PRIMES: Sequence[int] = _load_primes()


class PrimeLedger:
    __slots__ = ("_value", "_map", "_journal", "journal_path")
    def __init__(self, journal_path: pathlib.Path | None = None):
        self._value: int = 1
        self._map: dict[str, int] = {}
        self._journal: list[tuple[str, int]] = []
        self.journal_path = journal_path
        if journal_path and journal_path.exists():
            self._replay_journal()

    def register(self, symbol: str) -> int:
        if symbol not in self._map:
            idx = len(self._map)
            if idx >= len(_SMALL_PRIMES):
                raise RuntimeError("Prime pool exhausted (>664 k symbols)")
            self._map[symbol] = _SMALL_PRIMES[idx]
        return self._map[symbol]

    def write(self, symbol: str) -> None:
        p = self.register(symbol)
        self._value *= p
        self._journal.append((symbol, +1))
        self._flush()

    def check(self, symbol: str) -> bool:
        p = self._map.get(symbol)
        return p is not None and self._value % p == 0

    @property
    def size(self) -> int:
        return len(self._map)

    def _flush(self) -> None:
        if self.journal_path:
            self.journal_path.write_text("\n".join(f"{s},{d}" for s, d in self._journal))

    def _replay_journal(self) -> None:
        for line in self.journal_path.read_text().splitlines():
            symbol, delta = line.strip().split(",")
            p = self.register(symbol)
            if int(delta) == 1:
                self._value *= p
            else:
                if self._value % p == 0:
                    self._value //= p


# ---------------------------------------------------------------------------
# 2.  Energy constants (μJ scale, patent claim 7a)
# ---------------------------------------------------------------------------
FLOP_ENERGY_PJ = 0.4                       # 22-nm MAC
DIM            = 128
μJ_PER_FLOP    = FLOP_ENERGY_PJ * (DIM * DIM) / 1e6
μJ_PRIME_BASE  = 0.05                      # sub-linear penalty


# ---------------------------------------------------------------------------
# 3.  Continuous cache (unchanged maths, only style)
# ---------------------------------------------------------------------------
class ContinuousCache:
    def __init__(self, dim: int = 128) -> None:
        self.dim = dim
        self.x: List[float] = [0.0] * dim
        self.projectors: List[List[List[float]]] = []

    def add_projector(self) -> None:
        v = self._random_unit_vector(self.dim)
        self.projectors.append([[v[i] * v[j] for j in range(self.dim)] for i in range(self.dim)])

    def expect(self, idx: int) -> float:
        proj, x = self.projectors[idx], self.x
        return sum(x[j] * proj[j][k] * x[k] for j in range(self.dim) for k in range(self.dim))

    def gradient_step(self, idx: int, target: float, lr: float = 0.05) -> None:
        proj = self.projectors[idx]
        pred = self.expect(idx)
        err  = target - pred
        grad = [2.0 * sum(proj[j][k] * self.x[k] for k in range(self.dim)) for j in range(self.dim)]
        for j in range(self.dim):
            self.x[j] += lr * err * grad[j]

    def energy(self) -> float:
        return sum(v * v for v in self.x)

    @staticmethod
    def _random_unit_vector(dim: int) -> List[float]:
        v = [random.gauss(0, 1) for _ in range(dim)]
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]


# ---------------------------------------------------------------------------
# 4.  Memory substrates (cycle length in minutes, honest drift, μJ energy)
# ---------------------------------------------------------------------------
class TransformerMemory:
    def __init__(self, dim: int = 128) -> None:
        self.cache = ContinuousCache(dim)
        self.sym2idx: dict[str, int] = {}

    def observe(self, symbol: str, truth: float) -> None:
        idx = self.sym2idx.setdefault(symbol, len(self.sym2idx))
        if idx == len(self.cache.projectors):
            self.cache.add_projector()
        self.cache.gradient_step(idx, truth)

    def query(self, symbol: str) -> float:
        idx = self.sym2idx.get(symbol)
        return self.cache.expect(idx) if idx is not None else 0.0

    def energy(self) -> float:
        return μJ_PER_FLOP


class DualSubstrateMemory:
    def __init__(self, dim: int = 128, cycle_minutes: float = 15.0) -> None:
        self.continuous = ContinuousCache(dim)
        self.discrete   = PrimeLedger()
        self.sym2idx: dict[str, int] = {}
        self.cycle_minutes = cycle_minutes
        self.cycle_steps   = 0
        self.step          = 0

    def observe(self, symbol: str, truth: float) -> None:
        idx = self.sym2idx.setdefault(symbol, len(self.sym2idx))
        if idx == len(self.continuous.projectors):
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

    def query(self, symbol: str) -> tuple[float, bool]:
        idx = self.sym2idx.get(symbol)
        if idx is None:
            return 0.0, False
        return self.continuous.expect(idx), self.discrete.check(symbol)

    def energy(self) -> float:
        return μJ_PER_FLOP + μJ_PRIME_BASE * math.log(self.discrete.size + 1)


# ---------------------------------------------------------------------------
# 5.  Simulation loop (generator for live Streamlit bar)
# ---------------------------------------------------------------------------
@dataclass
class MetricSnapshot:
    minute: float
    recall: float
    drift: float
    energy: float


def simulate_memory(
    memory: TransformerMemory | DualSubstrateMemory,
    *,
    duration_minutes: int = 25,
    tokens_per_minute: int = 60,
    recall_threshold: float = 0.5,
) -> Iterator[tuple[float, list[MetricSnapshot]]]:
    steps = duration_minutes * tokens_per_minute
    names = ["Alice", "Bob", "Charlie", "Delta", "Echo"] * 20
    rng   = random.Random(42)
    seen: dict[str, int] = {}

    if isinstance(memory, DualSubstrateMemory):
        memory.cycle_steps = int(memory.cycle_minutes * tokens_per_minute)

    snapshots: list[MetricSnapshot] = []

    for t in range(1, steps + 1):
        symbol = rng.choice(names)
        count  = seen.get(symbol, 0)
        truth  = 1.0 if count == 0 else 0.7
        seen[symbol] = count + 1

        memory.observe(symbol, truth)

        expected = memory.query(symbol)[0] if isinstance(memory, DualSubstrateMemory) else memory.query(symbol)
        recall   = 1.0 if expected >= recall_threshold else 0.0
        drift    = abs(expected - 1.0)          # hard truth
        energy   = memory.energy()
        minute   = t / tokens_per_minute
        snapshots.append(MetricSnapshot(minute, recall, drift, energy))

        if t % tokens_per_minute == 0:
            yield minute, snapshots[-tokens_per_minute:]
