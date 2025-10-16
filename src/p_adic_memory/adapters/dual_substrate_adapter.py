"""Optional local transformers adapter with dual-substrate augmentation."""

from __future__ import annotations

import warnings
from importlib.metadata import PackageNotFoundError
from typing import Callable, Dict

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

try:  # pragma: no cover - optional dependency
    from transformers import BitsAndBytesConfig
except ImportError:  # pragma: no cover - optional dependency
    BitsAndBytesConfig = None

from p_adic_memory import DualSubstrate
from ..memory import POLICY
from ..prompt_frame import chatify, clean_out

__all__ = ["DualSubstrateGenerator"]

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


def _filter_gen_kwargs(kwargs: Dict[str, object], pad_id: int, eos_id: int) -> Dict[str, object]:
    allowed = {key: kwargs[key] for key in kwargs if key in _ALLOWED_GEN_KW}
    allowed.setdefault("pad_token_id", pad_id)
    allowed.setdefault("eos_token_id", eos_id)
    allowed.setdefault("max_new_tokens", 128)
    return allowed


class DualSubstrateGenerator:
    """Local HF-compatible generator that mirrors the notebook harness."""

    def __init__(
        self,
        model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        *,
        mem_dim: int = 128,
        cycle_minutes: int = 15,
    ) -> None:
        qconf = None
        if BitsAndBytesConfig is not None:
            qconf = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
        self.tok = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        load_kwargs = {
            "device_map": "auto",
            "trust_remote_code": True,
        }
        if qconf is not None:
            load_kwargs["quantization_config"] = qconf
        try:
            self.model = AutoModelForCausalLM.from_pretrained(model_name, **load_kwargs)
        except (PackageNotFoundError, ModuleNotFoundError) as exc:
            if "bitsandbytes" not in str(exc).lower():
                raise
            warnings.warn(
                "bitsandbytes is unavailable; loading the model without 4-bit quantization.",
                RuntimeWarning,
            )
            load_kwargs.pop("quantization_config", None)
            load_kwargs["device_map"] = "cpu"
            self.model = AutoModelForCausalLM.from_pretrained(model_name, **load_kwargs)
        self.mem = DualSubstrate(dim=mem_dim, cycle=cycle_minutes * 60)

    def _augment_with_memory(self, user_text: str) -> str:
        for idx, token in enumerate(user_text.split()):
            self.mem.observe(token, {"pos": idx % 11, "role": "ctx"})
        recent = user_text.split()[-64:]
        recalls = []
        for token in recent:
            query = self.mem.query(token)
            recalls.append(
                f"<mem exact={int(query.get('exact', False))} p={query.get('p', 0.0):.3f}>"
            )
        return f"{POLICY}\n<memory hidden='true'>{' '.join(recalls[:64])}</memory>\n\n{user_text}"

    def generate(self, prompt: str, *, backend: Callable[[str], str] | None = None, **gen_kwargs) -> str:
        """Generate text optionally delegating to a backend for final decoding."""

        augmented = self._augment_with_memory(prompt)
        chat_prompt = chatify(augmented) if backend is None else augmented

        inputs = self.tok(chat_prompt, return_tensors="pt").to(self.model.device)
        gkw = _filter_gen_kwargs(gen_kwargs, self.tok.eos_token_id, self.tok.eos_token_id)
        with torch.inference_mode():
            out = self.model.generate(**inputs, **gkw)
        gen_ids = out[0][inputs["input_ids"].shape[1]:]
        text = self.tok.decode(gen_ids, skip_special_tokens=True)
        return clean_out(text)
