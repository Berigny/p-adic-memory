"""Prompt wrapping utilities shared across frontends."""

from __future__ import annotations

import re

__all__ = ["chatify", "clean_out"]

_BAD_ANGLE = re.compile(r"<[^>]{0,200}>")

SYS = (
    "Follow instructions exactly. Never repeat the prompt. "
    "Never invent facts. If uncertain, output 'UNKNOWN'."
)
FEWSHOT = "Only output: TIME=9:00; PRIME=2.\nTIME=9:00; PRIME=2\n"


def chatify(user_text: str) -> str:
    """Apply the shared system and few-shot framing to ``user_text``."""

    return f"{SYS}\n\n{FEWSHOT}\n{user_text}".strip()


def clean_out(text: str) -> str:
    """Remove any leaked XML-like tags and trim whitespace."""

    return _BAD_ANGLE.sub("", (text or "")).strip()
