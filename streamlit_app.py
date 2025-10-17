"""Minimal Streamlit interface for the p-adic memory harness."""

from __future__ import annotations

import streamlit as st

import importlib.util
import sys
from pathlib import Path

if importlib.util.find_spec("p_adic_memory") is None:  # pragma: no cover - runtime import shim
    project_root = Path(__file__).resolve().parent
    src_dir = project_root / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))

from p_adic_memory.backends import GEMINI_MODEL, gemini_generate_text
from p_adic_memory.harness import baseline_generate, dual_generate

st.set_page_config(
    page_title="p-adic Memory Test Harness",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("Dual-Substrate A/B Harness")
st.caption("Run the same prompt against the baseline and memory-augmented paths.")

prompt = st.text_area("Prompt", height=150)
mode = st.radio("Mode", ("Baseline", "Dual"))

if st.button("Run", type="primary"):
    if prompt.strip():
        with st.spinner("Generating response..."):
            try:
                if mode == "Baseline":
                    output = baseline_generate(prompt, backend=gemini_generate_text)
                else:
                    output = dual_generate(prompt, backend=gemini_generate_text)
            except RuntimeError as exc:
                st.error(str(exc))
            else:
                st.subheader("Response")
                st.code(output or "<empty>")
    else:
        st.warning("Please enter a prompt before running the harness.")

st.sidebar.title("Backend")
st.sidebar.info(f"Gemini model: `{GEMINI_MODEL}` (via google.colab.ai)")
st.sidebar.caption(
    "To run locally without Colab, supply a custom backend callable to ``baseline_generate``/``dual_generate``."
)
