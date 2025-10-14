import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from p_adic_memory import DualSubstrate

_ALLOWED_GEN_KW = {
    "do_sample",
    "temperature",
    "top_p",
    "top_k",
    "repetition_penalty",
    "no_repeat_ngram_size",
    "max_new_tokens",
    "min_new_tokens",
    "early_stopping",
    "length_penalty",
    "eos_token_id",
    "pad_token_id",
    "num_beams",
    "num_beam_groups",
    "diversity_penalty",
    "return_dict_in_generate",
    "output_scores",
}


def _filter_gen_kwargs(kwargs, pad_id, eos_id):
    out = {k: v for k, v in kwargs.items() if k in _ALLOWED_GEN_KW}
    out.setdefault("pad_token_id", pad_id)
    out.setdefault("eos_token_id", eos_id)
    out.setdefault("max_new_tokens", 128)
    return out


class DualSubstrateGenerator:
    def __init__(self, model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0", mem_dim=128, cycle_minutes=15):
        qconf = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
        self.tok = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            trust_remote_code=True,
            quantization_config=qconf,
        )
        self.mem = DualSubstrate(dim=mem_dim, cycle_minutes=cycle_minutes)

    def _augment_with_memory(self, user_text: str) -> str:
        for i, tok_txt in enumerate(user_text.split()):
            self.mem.observe(tok_txt, {"pos": i % 11, "role": "ctx"})
        recent = user_text.split()[-64:]
        recalls = []
        for t in recent:
            q = self.mem.query(t)
            recalls.append(f"<mem exact={int(q.get('exact', False))} p={q.get('p', 0.0):.3f}>")
        policy = (
            "<memory-policy>"
            "Use memory facts if present. If memory and the prompt disagree, prefer memory. "
            "Output only what is requested; never repeat the question."
            "</memory-policy>"
        )
        return f"{policy}\n<memory>{' '.join(recalls[:64])}</memory>\n\n{user_text}"

    def generate(self, prompt: str, *, chat_wrapper=None, **gen_kwargs) -> str:
        text = self._augment_with_memory(prompt)
        if callable(chat_wrapper):
            text = chat_wrapper(text)

        inputs = self.tok(text, return_tensors="pt").to(self.model.device)
        gkw = _filter_gen_kwargs(gen_kwargs, self.tok.eos_token_id, self.tok.eos_token_id)
        with torch.inference_mode():
            out = self.model.generate(**inputs, **gkw)
        return self.tok.decode(out[0], skip_special_tokens=True).strip()
