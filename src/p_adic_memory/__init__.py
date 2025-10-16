"""Public API for the anonymised dual-substrate benchmark harness."""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("p-adic-memory")
except PackageNotFoundError:  # editable installs during dev
    __version__ = "0.0.0"

# Re-export the stable API surface
from .dual_substrate import DualSubstrate, DualSubstrateMemory, available_models, build_model
from .harness import baseline_generate, dual_generate
from .prompt_frame import chatify, clean_out
from .memory import POLICY, build_mem_blob

__all__ = [
    "DualSubstrate",
    "DualSubstrateMemory",
    "available_models",
    "build_model",
    "baseline_generate",
    "dual_generate",
    "chatify",
    "clean_out",
    "POLICY",
    "build_mem_blob",
    "__version__",
]
