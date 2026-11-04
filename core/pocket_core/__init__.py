"""Pocket device core: a backend abstraction shared by the CLI, the MCP server and the Pocket TUI."""
from .backend import POWER_PROFILES, Backend, get_backend

__version__ = "0.1.0"
__all__ = ["Backend", "POWER_PROFILES", "get_backend", "__version__"]
