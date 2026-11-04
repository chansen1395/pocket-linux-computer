"""`pocket-mcp`: the backend's capabilities as MCP tools for Claude Code, over stdio.

Register with:  claude mcp add pocket -- pocket-mcp   (or see core/claude-mcp.json)
"""
import argparse
import os
import sys
from typing import Any

try:  # mcp >= 2.0 renamed FastMCP to MCPServer; the decorator API is the same
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:  # mcp 1.x import path, kept but untested (pyproject requires mcp 2.3 or newer)
    from mcp.server.fastmcp import FastMCP

from .backend import Backend, get_backend
from .cli import status_summary

server = FastMCP(
    "pocket",
    instructions="Inspect and control the Pocket device, a Raspberry Pi 5 portable computer. The *_status, "
                 "snapshot_list, kb_search and audit_tail tools are read-only; the others change the device. "
                 "Call snapshot_create before risky system changes. Every result is a plain JSON object; "
                 "failures are reported as ok=false with a message, never as errors.",
)
_backend: Backend | None = None


def backend() -> Backend:
    global _backend
    if _backend is None:
        _backend = get_backend()
    return _backend


@server.tool()
def device_status() -> dict[str, Any]:
    """Board model, SoC temperature (C), throttling flags from vcgencmd, CPU MHz, load averages, RAM in MB,
    disks in GB, uptime in seconds and hostname."""
    return backend().device_status()


@server.tool()
def power_status() -> dict[str, Any]:
    """Power source (usb-c, battery or unknown), battery percent, input volts, estimated amps and watts,
    every PMIC rail reading, and the active power profile."""
    return backend().power_status()


@server.tool()
def net_status() -> dict[str, Any]:
    """Interfaces with IPv4 and link state, active Wi-Fi SSID and signal,
    whether the local ad-blocking resolver answers (resolver_ok) and the default route's interface."""
    return backend().net_status()


@server.tool()
def snapshot_list() -> list[dict[str, Any]]:
    """Read-only btrfs snapshots of / under /.snapshots as {name, created}, oldest first."""
    return backend().snapshot_list()


@server.tool()
def snapshot_create(label: str = "manual") -> dict[str, Any]:
    """Take a read-only btrfs snapshot of / named YYYYmmdd-HHMMSS-<label>. Do this before risky changes
    (apt, /etc, /boot). Returns ok=false with message "root is not btrfs" when snapshots are unavailable."""
    return backend().snapshot_create(label)


@server.tool()
def resolver_status() -> dict[str, Any]:
    """State of Blocky, the local ad-blocking DNS resolver: enabled, blocked query count (None unless
    metrics are on) and a detail line."""
    return backend().resolver_status()


@server.tool()
def resolver_set(enabled: bool) -> dict[str, Any]:
    """Enable (true) or pause (false) ad blocking. A pause lasts 15 minutes, then Blocky re-enables itself."""
    return backend().resolver_set(enabled)


@server.tool()
def kb_search(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Full-text search of the offline Kiwix library (Wikipedia, WikiMed, iFixit, ...). Each hit has a title,
    a url on the local kiwix-serve and a snippet. Empty when kiwix-serve is not running."""
    return backend().kb_search(query, limit)


@server.tool()
def audit_tail(n: int = 20) -> list[str]:
    """The last n lines of ~/.pocket/audit.log: every Bash command Claude Code has run on this device."""
    return backend().audit_tail(n)


@server.tool()
def set_power_profile(name: str) -> dict[str, Any]:
    """Switch the power profile: performance (no CPU cap), balanced (ondemand governor) or endurance
    (powersave governor, CPU capped at 1.5 GHz). Returns ok=false with the reason when sysfs cannot be written."""
    return backend().set_power_profile(name)


@server.tool()
def set_brightness(pct: int) -> dict[str, Any]:
    """Set the display backlight to pct percent (0-100, clamped)."""
    return backend().set_brightness(pct)


@server.resource("pocket://status", name="status", description="One-line device status summary", mime_type="text/plain")
def status_resource() -> str:
    b = backend()
    return status_summary(b.device_status(), b.power_status(), b.net_status())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pocket-mcp", description="MCP server for the Pocket device, over stdio. "
                                "Register it with: claude mcp add pocket -- pocket-mcp")
    p.add_argument("--fake", action="store_true", help="use the fake backend (same as POCKET_BACKEND=fake)")
    if p.parse_args(argv).fake:
        os.environ["POCKET_BACKEND"] = "fake"
    server.run(transport="stdio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
