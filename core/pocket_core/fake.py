"""Deterministic in-memory backend: used on non-Pi machines, in tests and by the Pocket TUI demo."""
from __future__ import annotations

from datetime import datetime, timedelta

from .backend import POWER_PROFILES, snapshot_name

KIWIX = "http://127.0.0.1:8090"


class FakeBackend:
    def __init__(self) -> None:
        self.profile = "balanced"
        self.brightness = 70
        self.resolver_enabled = True
        self._clock = datetime(2026, 10, 16, 21, 0, 0)  # advances one minute per snapshot
        self.snapshots = [
            {"name": "20261010-083000-first-nvme-boot", "created": "2026-10-10T08:30:00"},
            {"name": "20261011-120000-claude", "created": "2026-10-11T12:00:00"},
            {"name": "20261012-193000-pre-apt", "created": "2026-10-12T19:30:00"},
            {"name": "20261014-071500-claude", "created": "2026-10-14T07:15:00"},
            {"name": "20261015-223000-before-kernel", "created": "2026-10-15T22:30:00"},
        ]
        self.audit = [
            "2026-10-16T19:02:11-07:00\tsudo apt update",
            "2026-10-16T19:03:40-07:00\tsudo apt install -y kiwix-tools",
            "2026-10-16T19:05:02-07:00\tsystemctl --user status syncthing",
            "2026-10-16T19:07:18-07:00\tpocketctl snapshot create pre-blocky",
            "2026-10-16T19:07:30-07:00\tsudo systemctl restart blocky",
            "2026-10-16T19:09:55-07:00\tsystemctl status kiwix",
        ]

    def device_status(self) -> dict:
        return {
            "model": "Raspberry Pi 5 Model B Rev 1.0", "temp_c": 48.2, "throttled_hex": "0x0", "throttle_flags": [],
            "cpu_mhz": 2400 if self.profile == "performance" else 1500, "load": [0.42, 0.31, 0.25],
            "mem_total_mb": 4045, "mem_avail_mb": 2150,
            "disks": [{"mount": "/", "total_gb": 1863.0, "used_gb": 23.4},
                      {"mount": "/boot/firmware", "total_gb": 0.5, "used_gb": 0.1}],
            "uptime_s": 11520, "hostname": "pocket",
        }

    def power_status(self) -> dict:
        rails = {"VDD_CORE_A": 0.75, "VDD_CORE_V": 0.725, "3V3_SYS_A": 0.022, "3V3_SYS_V": 3.308,
                 "1V8_SYS_A": 0.199, "1V8_SYS_V": 1.802, "EXT5V_V": 5.086, "BATT_V": 0.0}
        return {"source": "usb-c", "battery_pct": None, "volts": 5.086, "amps": 0.83, "watts": 4.2,
                "rails": rails, "profile": self.profile}

    def net_status(self) -> dict:
        return {
            "interfaces": [{"name": "eth0", "ip": None, "state": "down"},
                           {"name": "wlan0", "ip": "192.0.2.42", "state": "up"}],
            "wifi": {"ssid": "ExampleNet", "signal": 71},
            "resolver_ok": True, "default_if": "wlan0",
        }

    def snapshot_list(self) -> list[dict]:
        return sorted(self.snapshots, key=lambda s: s["name"])

    def snapshot_create(self, label: str) -> dict:
        self._clock += timedelta(minutes=1)
        name = snapshot_name(label, self._clock)
        self.snapshots.append({"name": name, "created": self._clock.isoformat(timespec="seconds")})
        return {"name": name, "ok": True, "message": f"created /.snapshots/{name} (fake)"}

    def resolver_status(self) -> dict:
        return {"enabled": self.resolver_enabled, "blocked_recent": 1342,
                "detail": "blocking enabled" if self.resolver_enabled else "blocking disabled, re-enables in 900 s"}

    def resolver_set(self, enabled: bool) -> dict:
        self.resolver_enabled = bool(enabled)
        return {"enabled": self.resolver_enabled, "ok": True, "message": self.resolver_status()["detail"]}

    def kb_search(self, query: str, limit: int = 10) -> list[dict]:
        q = " ".join(query.split()) or "empty"
        slug = q.replace(" ", "_").title()
        titles = [q.title(), f"{q.title()} (overview)", f"History of {q}"]
        return [{"title": t, "url": f"{KIWIX}/content/wikipedia_en_all_maxi_2024-01/A/{slug}{'' if i == 0 else f'_{i}'}",
                 "snippet": f"{t}: fake result {i + 1} for '{q}' from the offline Wikipedia set."}
                for i, t in enumerate(titles)][:max(0, limit)]

    def audit_tail(self, n: int = 20) -> list[str]:
        return self.audit[-n:] if n > 0 else []

    def set_power_profile(self, name: str) -> dict:
        if name not in POWER_PROFILES:
            return {"profile": self.profile, "ok": False,
                    "message": f"unknown profile {name!r}; use one of {', '.join(POWER_PROFILES)}"}
        self.profile = name
        return {"profile": name, "ok": True, "message": f"profile {name} applied (fake)"}

    def set_brightness(self, pct: int) -> dict:
        self.brightness = max(0, min(100, int(pct)))
        return {"pct": self.brightness, "ok": True, "message": "set (fake)"}
