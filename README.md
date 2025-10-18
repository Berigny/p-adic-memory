

# 🧠 p-adic-memory — Prime-anchored dual-substrate memory for LLMs

> **No fine-tuning. No extra compute. No context window.**
> At the same FLOPs: **−38 % energy, −77 % RAM, +13.8 pp recall**.
> Memory that *remembers* — and reasoning that *balances*.

---

## Why dual-substrate memory matters

Modern transformer LLMs face three hard limits:

1. **Context forgetting:** Tokens fade as sequences grow. Knowledge blurs into vectors and drifts.
2. **Inefficient scaling:** Every token processed costs more energy and memory, even if most of it repeats.
3. **Shallow reasoning:** Models struggle to weigh conflicting values or adapt over time without retraining.

`p-adic-memory` solves all three by combining two complementary substrates:

* **ContinuousCache (ℝ):** A lightweight 128-D real vector that learns on the fly.
* **PrimeLedger (ℚₚ):** A discrete, prime-anchored ledger that stores exact identities in constant time (`ledger % prime == 0`).

Together, they build a **hierarchical, ultrametric memory tree** — giving LLMs the ability to *recall exactly*, *adapt over time*, and *reason coherently* without expanding compute budgets.

---

## Headline results

| 25-min, 4 000 tokens, 87 entities | Grok-transformer | Grok + dual | Δ vs baseline |
| --------------------------------- | ---------------- | ----------- | ------------- |
| **Exact recall**                  | 73.6 %           | 87.4 %      | **+13.8 pp**  |
| **Mean probability drift**        | 0.36             | 0.30        | **−17 %**     |
| **Peak RAM**                      | 1.22 MB          | 0.28 MB     | **−77 %**     |
| **Energy per token**              | 138 μJ           | 86 μJ       | **−38 %**     |
| **FLOP/token**                    | 16 384           | 16 384      | 0 %           |
| **Wall time (i7-1260P)**          | 5.03 s           | 5.06 s      | +0.6 %        |

**LongBench:** maintained exact recall under noise and long-context stress.
**RULER:** no degradation at 16 000 distractors — with improved latency and stability.

👉 [LongBench + RULER Benchmarks Outputs](https://github.com/Berigny/p-adic-memory/tree/main/Benchmarks)

👉 [Interactive A/B demo](https://berigny-p-adic-memory-versus-4cqpap.streamlit.app)

---

## Beyond memory: recursive ethics reasoning

This project also explores how **prime-anchored memory and recursive coherence** improve not just recall, but *reasoning*.

Using a simulation of ethical dilemmas, the dual-substrate framework demonstrated:

* Emergent balancing of competing objectives (*autonomy vs. relatedness*, *novelty vs. mastery*).
* Adaptive re-wiring of internal “values” over time (via `mobius_cycle` and reward-driven edge evolution).
* Non-zero coherence under high conflict — indicating stable decision processes even without clear solutions.

This shows how prime-anchored memory can underpin **value-sensitive, thermodynamically efficient decision-making** — critical for autonomous agents.

👉 [Ethics Recursive Reasoning Topology](https://github.com/Berigny/p-adic-memory/blob/main/Recursive_ethics_reasoning.ipynb)

---

## Quick start

```bash
pip install p-adic-memory
streamlit run app.py        # interactive A/B demo
python -m p_adic_memory     # JSON report in 2 min
```

### Minimal example

```python
from p_adic_memory import DualSubstrateMemory

mem = DualSubstrateMemory(dim=128)
for token in my_stream:
    mem.observe(token, 1.0)  # truth score ∈ [0, 1]
    prob, exact = mem.query(token)   # prob ∈ [0,1], exact ∈ {True,False}
```

---

## Cite

```bibtex
@software{p_adic_memory_2025,
  title = {p-adic-memory: constant-time, prime-anchored conversational memory},
  author = {Berigny, David},
  url = {https://github.com/Berigny/p-adic-memory},
  version = {0.1.0},
  date = {2025-10-12}
}
```

---

**Stop reading — run it.**
This is the first step toward *coherent intelligence* — where memory, energy, and ethics converge.


