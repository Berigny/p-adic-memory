# src/p_adic_memory/harness.py
from __future__ import annotations
import os, re, torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

DEFAULT_MODEL = os.getenv("PAM_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
DEFAULT_REV   = os.getenv("PAM_REV", None)  # pin commit if you want exact reproducibility

GEN_KW = dict(
    do_sample=False, temperature=0.0, top_p=1.0,
    repetition_penalty=1.15, no_repeat_ngram_size=3,
    max_new_tokens=64
)

BAD_ANGLE = re.compile(r"<[^>]{0,200}>")


def clean_output(s: str) -> str:
    return BAD_ANGLE.sub("", s).strip()

def load_model(model_name: str = DEFAULT_MODEL, revision: str | None = DEFAULT_REV):
    qconf = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                               bnb_4bit_use_double_quant=True, bnb_4bit_quant_type="nf4")
    tok = AutoTokenizer.from_pretrained(model_name, use_fast=True, revision=revision)
    mdl = AutoModelForCausalLM.from_pretrained(
        model_name, device_map="auto", trust_remote_code=True,
        quantization_config=qconf, revision=revision
    )
    # fill pad/eos for deterministic generation
    GEN_KW["pad_token_id"] = tok.eos_token_id
    GEN_KW["eos_token_id"] = tok.eos_token_id
    return tok, mdl

def chatify(tok, user_text: str) -> str:
    msgs = [
        {"role": "system", "content": "Follow instructions exactly. Never repeat the prompt. Never invent facts."},
        {"role": "user", "content": "Only output: TIME=9:00; PRIME=2."},
        {"role": "assistant", "content": "TIME=9:00; PRIME=2"},
        {"role": "user", "content": user_text},
    ]
    return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)

def generate(tok, mdl, user_text: str, **overrides):
    text = chatify(tok, user_text)
    ids = tok(text, return_tensors="pt").to(mdl.device)
    kw = {**GEN_KW, **overrides}
    with torch.inference_mode():
        out = mdl.generate(**ids, **kw)
    gen_ids = out[0][ids["input_ids"].shape[1]:]
    s = tok.decode(gen_ids, skip_special_tokens=True).strip()
    return clean_output(s)
