PYTHON ?= python
PYTEST ?= pytest

.PHONY: help install test demo bench-dual bench-transformer bench-nolima bench-all score streamlit-spec streamlit-app streamlit-versus

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
	@echo "  streamlit-spec     Print the Streamlit spec structure"
	@echo "  streamlit-app      Install extras and launch the Streamlit UI"
	@echo "  streamlit-versus   Install extras and launch the versus Streamlit UI"

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

streamlit-spec:
	PYTHONPATH=src $(PYTHON) -c "from p_adic_memory.streamlit_spec import get_streamlit_spec; import pprint; pprint.pprint(get_streamlit_spec())"

streamlit-app:
	$(PYTHON) -m pip install -r requirements.txt streamlit
	PYTHONPATH=src streamlit run streamlit_app.py

streamlit-versus:
	$(PYTHON) -m pip install -r requirements.txt streamlit
	PYTHONPATH=src streamlit run versus.py
