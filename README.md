# Dual-substrate long-context drift benchmark (anonymised)

## What’s included

* Minimal demo (Python) with a 128-D continuous cache and a discrete, append-only ledger.
* Benchmark scripts to pit this demo against baselines (“standard transformer”, “NoLiMa”) on identical prompts.
* Deterministic seeds, logs, and scoring utilities.

## What’s measured

* **Recall@k** of seeded facts over rolling turns (0, 10, 20, 25 minutes equivalent tokens).
* **Drift score** (contradictions vs ground truth over time).
* **Efficiency**: tokens processed and simple energy proxy (tokens × operations), wall-clock.

## Repro steps

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python demo.py             # runs the dual-substrate harness
python bench.py --model baseline_transformer
python bench.py --model nolima_baseline
python bench.py --model dual_substrate
python score.py logs/*.jsonl > results.csv
```

Optional flags:

* `python bench.py --model dual_substrate --cycle 1200` — change cycle length.
* `python bench.py --model dual_substrate --no-shuffle` — disable Möbius shuffle for ablation.

IP note: this is an anonymised harness for verification; core routines are withheld.

## Benchmark protocol (what xAI asked for)

* **Dataset:** Rolling dialogue generator with seeded entities/facts; periodic cross-reference checks.
* **Turns:** 2,000–5,000 tokens; checkpoints at fixed token budgets (e.g., 1k, 2k, 3k…).
* **Metrics:** Recall@k, drift/contradiction rate, retention half-life, tokens/sec, ops proxy.
* **Controls:** Same prompts, fixed random seed, identical stop criteria; publish transcripts + hashes.
* **Outputs:** `results.csv`, full logs, and a short summary table.

## Share vs hold back

**Share (safe):**

* The posted `DualSubstrate` scaffold, fixed 128-D cache, append-only ledger interface.
* Möbius “shuffle” as a blind permutation (no revealing cycle/automorphism logic).
* Bench harness, metrics, deterministic seed, transcripts, hashes.

**Hold back:**

* Actual prime-ledger update rule (beyond append).
* Real cycle/automorphism engine (the Möbius schedule and mappings).
* Any constants/tables that enable re-derivation of the coupling.

## Dataset

The ready-to-use dataset lives at `dataset.jsonl` and includes F1–F12 seeded facts and CP1–CP6 contradiction probes.

## Logs & scoring

Benchmark runs emit JSONL logs under `logs/`. `score.py` consolidates them into a CSV for publication-ready reporting.
