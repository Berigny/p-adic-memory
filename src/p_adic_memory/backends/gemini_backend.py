"""Gemini backend adapter used in Colab Pro/Pro+ flows."""

from __future__ import annotations

from typing import Any

__all__ = ["MODEL", "generate_text"]

MODEL = "google/gemini-2.5-flash"

try:  # pragma: no cover - colab-only dependency
    from google.colab import ai as _colab_ai
except Exception:  # pragma: no cover - when running outside Colab
    _colab_ai = None  # type: ignore


def _get_client(client: Any | None) -> Any:
    if client is not None:
        return client
    if _colab_ai is None:
        raise RuntimeError(
            "google.colab.ai is unavailable; the Gemini backend can only run inside Colab."
        )
    return _colab_ai


def generate_text(prompt: str, *, model_name: str = MODEL, client: Any | None = None) -> str:
    """Invoke the Gemini text generation endpoint."""

    colab_ai = _get_client(client)
    return colab_ai.generate_text(prompt, model_name=model_name).strip()
