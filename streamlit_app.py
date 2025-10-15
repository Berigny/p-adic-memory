"""Minimal Streamlit interface for the p-adic memory harness."""

from __future__ import annotations

import sys
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st
from p_adic_memory.harness import load_model, generate

# --- Page Config ---
st.set_page_config(
    page_title="p-adic Memory Test Harness",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Model Loading ---
@st.cache_resource
def get_model():
    """Load and cache the model."""
    return load_model()

tok, mdl = get_model()

# --- UI Components ---
st.title("p-adic Memory Test Harness")
st.caption("A simple interface to test the dual-substrate memory model.")

# --- Test Case Loading ---
try:
    with open("tests/test_cases.json") as f:
        test_cases = json.load(f)

    test_case_prompts = {case["id"]: case["prompt"] for case in test_cases}
    selected_test_case = st.selectbox("Choose a test case", options=list(test_case_prompts.keys()))
    user_text = st.text_area("Or enter your own prompt here:", value=test_case_prompts[selected_test_case], height=150)
except FileNotFoundError:
    st.error("`tests/test_cases.json` not found. Please create it to load test cases.")
    user_text = st.text_area("Enter your prompt here:", height=150)

if st.button("Generate Response", type="primary"):
    if user_text:
        with st.spinner("Generating response..."):
            response = generate(tok, mdl, user_text)
            st.subheader("Generated Response")
            st.markdown(response)
    else:
        st.warning("Please enter a prompt.")

# --- Sidebar ---
st.sidebar.title("About")
st.sidebar.info(
    "This application uses a shared harness to ensure consistent model outputs "
    "between the Streamlit app and the Colab notebook."
)
st.sidebar.title("Model Information")
st.sidebar.info(f"**Model:** `{mdl.config.name_or_path}`")
st.sidebar.info(f"**Tokenizer:** `{tok.name_or_path}`")