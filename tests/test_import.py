"""Sanity checks for the public package surface."""

import p_adic_memory as pam


def test_public_api_exposed() -> None:
    assert hasattr(pam, "DualSubstrate")
    assert hasattr(pam, "build_model")
    assert hasattr(pam, "available_models")
    assert isinstance(pam.__version__, str)
