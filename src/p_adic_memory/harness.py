"""Unified baseline vs dual-substrate generation harness."""

from __future__ import annotations

from typing import Callable

from .memory import POLICY, build_mem_blob
from .prompt_frame import chatify, clean_out
from .backends.gemini_backend import generate_text as gemini_generate_text

__all__ = ["baseline_generate", "dual_generate"]

BackendFn = Callable[[str], str]


def _call_backend(prompt: str, backend: BackendFn | None) -> str:
    fn = backend or gemini_generate_text
    return fn(prompt)


def baseline_generate(user_text: str, *, backend: BackendFn | None = None) -> str:
    """Generate a response without memory augmentation."""

    prompt = chatify(user_text)
    return clean_out(_call_backend(prompt, backend))


def dual_generate(user_text: str, *, backend: BackendFn | None = None) -> str:
    """Generate a response with the dual-substrate memory shim enabled."""

    mem_blob = build_mem_blob(user_text)
    augmented = f"{POLICY}\n<memory hidden='true'>{mem_blob}</memory>\n\n{user_text}"
    prompt = chatify(augmented)
    return clean_out(_call_backend(prompt, backend))
