"""Lightweight DualSubstrate wrapper shared by notebook and app."""

from __future__ import annotations

from typing import Optional

__all__ = ["POLICY", "build_mem_blob"]

try:  # pragma: no cover - exercised in environments with the extension available
    from .dual_substrate import DualSubstrate
except Exception:  # pragma: no cover - fallback when extension is unavailable
    DualSubstrate = None  # type: ignore

_POLICIES = (
    "<memory-policy hidden='true'>Use memory facts if present. "
    "Never print memory tags. If conflict with the prompt, prefer memory." "</memory-policy>"
)
POLICY = "".join(_POLICIES)

_mem: Optional["DualSubstrate"]
if DualSubstrate is None:  # pragma: no cover - exercised when dependency missing
    _mem = None
else:  # pragma: no branch - trivial branch
    _mem = DualSubstrate(dim=128, cycle=900)


def build_mem_blob(prompt: str) -> str:
    """Derive a memory hint blob for the latest prompt tokens."""

    if _mem is None:
        return "<mem exact=0 p=0.000>"

    toks = prompt.split()
    for i, token in enumerate(toks):
        _mem.observe(token, {"pos": i % 11, "role": "ctx"})

    recent = toks[-64:]
    recalls = []
    for token in recent:
        query = _mem.query(token)
        recalls.append(
            f"<mem exact={int(query.get('exact', False))} p={query.get('p', 0.0):.3f}>"
        )
    return " ".join(recalls[:64])
