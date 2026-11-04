"""The backend contract the Pocket TUI codes against, and how the backend is chosen.

The real implementation lives in ``pocket_core`` (another package in this repo); this module
only describes it and falls back to the bundled fake when it is missing or ``--demo`` is given.
"""

from __future__ import annotations

import sys
from typing import Protocol


class Backend(Protocol):
    def device_status(self) -> dict:
        """{"model", "temp_c", "throttled_hex", "throttle_flags", "cpu_mhz", "load", "mem_total_mb",
        "mem_avail_mb", "disks": [{"mount", "total_gb", "used_gb"}], "uptime_s", "hostname"}"""

    def power_status(self) -> dict:
        """{"source": usb-c|battery|unknown, "battery_pct", "volts", "amps", "watts", "rails", "profile"}"""

    def net_status(self) -> dict:
        """{"interfaces": [{"name", "ip", "state"}], "wifi": {"ssid", "signal"}|None,
        "resolver_ok", "default_if"}"""

    def snapshot_list(self) -> list[dict]: ...            # [{"name", "created"}]
    def snapshot_create(self, label: str) -> dict: ...    # {"name", "ok", "message"}
    def resolver_status(self) -> dict: ...                # {"enabled", "blocked_recent", "detail"}
    def resolver_set(self, enabled: bool) -> dict: ...    # {"enabled", "ok"}
    def kb_search(self, query: str, limit: int = 10) -> list[dict]: ...   # [{"title", "url", "snippet"}]
    def audit_tail(self, n: int = 20) -> list[str]: ...
    def set_power_profile(self, name: str) -> dict: ...   # performance | balanced | endurance
    def set_brightness(self, pct: int) -> dict: ...


def load_backend(demo: bool = False) -> tuple[Backend, str]:
    """Return ``(backend, name)``: the pocket_core backend, or the fake when asked or unavailable."""
    if not demo:
        try:
            from pocket_core.backend import get_backend  # type: ignore[import-not-found]

            return get_backend(), "pocket_core"
        except Exception as exc:  # ImportError, or the real backend failing to start
            print(f"pocket_tui: pocket_core unavailable ({exc!r}); using the demo backend", file=sys.stderr)
    from .backend_fake import FakeBackend

    return FakeBackend(), "demo"
