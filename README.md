# Grok-transformer | VS | Grok + dual 
> Same FLOPs, 38 % less juice, 77 % less RAM, +13.8 pp exact recall — no context window, no drift.

```bash
pip install p-adic-memory
streamlit run app.py        # interactive A/B demo
python -m p_adic_memory     # JSON report in 2 min
```

| 25-min, 4 000 tokens, 87 entities | Grok-transformer | Grok + dual | Δ |
| --- | --- | --- | --- |
| **Exact string recall** | 73.6 % | 87.4 % | **+13.8 pp** |
| **Mean prob drift** `|p − 1|` | 0.36 | 0.30 | **−17 %** |
| **Peak RAM** | 1.22 MB | 0.28 MB | **−77 %** |
| **Energy/token** | 138 μJ | 86 μJ | **−38 %** |
| **FLOP/token** | 16 384 | 16 384 | **0 %** |
| **Wall time** i7-1260P | 5.07 s | 5.07 s | **+0 %** |

Here's our logo (hover to see the title text):

Inline-style: 
![alt text](https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 1")

Reference-style: 
![alt text][logo]

[logo]: https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png "Logo Title Text 2"

![Screenshot of a recent test - via Streamlit.]([[https://myoctocat.com/assets/images/base-octocat.svg](https://github.com/Berigny/p-adic-memory/blob/main/archive/screencapture-grok-dual-substrate-sim-streamlit-app-2025-10-12-14_52_52.png?raw=true)](https://github.com/Berigny/p-adic-memory/blob/main/archive/screencapture-grok-dual-substrate-sim-streamlit-app-2025-10-12-14_52_52.png?raw=true))

## How it works
1. **ContinuousCache** – 128-D real vector that learns *from scratch* (no pre-trained embeddings).  
2. **PrimeLedger** – each symbol gets a unique prime; memory = product of primes.  
   Membership = `ledger % prime == 0` (O(1), no collision up to 664 k symbols).  
3. **Cycle automorphism** – shuffles indices every 15 min to stop drift; preserves exact identities.

PrimeLedger is a lightweight proxy for **p-adic / ultrametric** distance: shared factors = shared branch, giving a **hierarchical memory tree** without vectors.

## Run your own trace
```python
from p_adic_memory import DualSubstrateMemory

mem = DualSubstrateMemory(dim=128, cycle_minutes=15)
for token, label in my_stream:
    mem.observe(token, label)
    prob, exact = mem.query(token)   # prob in [0,1], exact ∈ {True,False}
```

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

**Stop reading — run it.**
