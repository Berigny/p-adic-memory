"""Backend adapters for the p-adic memory harness."""

from .gemini_backend import MODEL as GEMINI_MODEL, generate_text as gemini_generate_text

__all__ = ["GEMINI_MODEL", "gemini_generate_text"]
