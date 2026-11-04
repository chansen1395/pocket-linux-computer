"""The Backend protocol, shared helpers and backend selection."""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Protocol

POWER_PROFILES = ("performance", "balanced", "endurance")


class Backend(Protocol):
    """Everything the CLI, the MCP server and PocketTui can ask of the device.

    Every method returns JSON-serializable dicts/lists and never raises: a value that cannot be
    read is None, an action that fails reports ok=False with a message.
    """

    def device_status(self) -> dict: ...
    def power_status(self) -> dict: ...
    def net_status(self) -> dict: ...
    def snapshot_list(self) -> list[dict]: ...
    def snapshot_create(self, label: str) -> dict: ...
    def resolver_status(self) -> dict: ...
    def resolver_set(self, enabled: bool) -> dict: ...
    def kb_search(self, query: str, limit: int = 10) -> list[dict]: ...
    def audit_tail(self, n: int = 20) -> list[str]: ...
    def set_power_profile(self, name: str) -> dict: ...
    def set_brightness(self, pct: int) -> dict: ...


def snapshot_name(label: str, when: datetime) -> str:
    """YYYYmmdd-HHMMSS-<label> with the label reduced to [A-Za-z0-9._-]."""
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", label.strip()).strip("-") or "manual"
    return when.strftime("%Y%m%d-%H%M%S-") + safe[:40]


def is_raspberry_pi() -> bool:
    try:
        return "raspberry pi" in Path("/proc/device-tree/model").read_bytes().decode("ascii", "replace").lower()
    except OSError:
        return False


def get_backend() -> Backend:
    """The Linux backend on a Raspberry Pi, the Fake backend anywhere else.

    POCKET_BACKEND=fake forces the fake; POCKET_BACKEND=linux forces the Linux backend (for a dry run
    on a non-Pi Linux box).
    """
    forced = os.environ.get("POCKET_BACKEND", "").strip().lower()
    if forced == "linux" or (not forced and sys.platform.startswith("linux") and is_raspberry_pi()):
        from .linux import LinuxBackend

        return LinuxBackend()
    from .fake import FakeBackend

    return FakeBackend()
