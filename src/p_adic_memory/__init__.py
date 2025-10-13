"""Public API for the anonymised dual-substrate benchmark harness."""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("p-adic-memory")
except PackageNotFoundError:  # editable installs during dev
    __version__ = "0.0.0"

# Re-export the stable API surface
from .dual_substrate import DualSubstrate, DualSubstrateMemory, available_models, build_model

__all__ = [
    "DualSubstrate",
    "DualSubstrateMemory",
    "available_models",
    "build_model",
    "__version__",
]
