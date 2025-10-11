PYTHON ?= python
PYTEST ?= pytest

.PHONY: help install test demo bench-dual bench-transformer bench-nolima bench-all score

help:
	@echo "Targets:"
	@echo "  install            Install Python dependencies via requirements.txt"
	@echo "  test               Run the pytest suite (PYTHONPATH=src)"
	@echo "  demo               Run the interactive demo harness"
	@echo "  bench-dual         Benchmark the dual substrate model"
	@echo "  bench-transformer  Benchmark the transformer baseline"
	@echo "  bench-nolima       Benchmark the NoLiMa-style baseline"
	@echo "  bench-all          Run all benchmark variants sequentially"
	@echo "  score              Aggregate logs into results.csv"

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	PYTHONPATH=src $(PYTEST)

demo:
	PYTHONPATH=src $(PYTHON) demo.py

bench-dual:
	PYTHONPATH=src $(PYTHON) bench.py --model dual_substrate

bench-transformer:
	PYTHONPATH=src $(PYTHON) bench.py --model baseline_transformer

bench-nolima:
	PYTHONPATH=src $(PYTHON) bench.py --model nolima_baseline

bench-all: bench-transformer bench-nolima bench-dual

score:
	$(PYTHON) score.py logs/*.jsonl > results.csv
