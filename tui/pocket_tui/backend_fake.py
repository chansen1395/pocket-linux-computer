"""A deterministic stand-in for pocket_core: development on any machine, and the tests."""

from __future__ import annotations

import itertools

_KB = [
    ("Cardiopulmonary resuscitation", "wikipedia_en_medicine",
     "Chest compressions with rescue breaths keep blood moving until circulation returns."),
    ("First aid", "wikipedia_en_all",
     "Immediate help given to a person with a minor or serious illness or injury."),
    ("Water purification", "wikipedia_en_all",
     "Boiling, filtration, chlorine and UV each remove or kill pathogens in drinking water."),
    ("Hypothermia", "wikipedia_en_medicine",
     "Core temperature below 35 C: remove wet clothing, insulate, warm the trunk first."),
    ("Raspberry Pi", "wikipedia_en_all",
     "Small single-board computers developed in the UK by the Raspberry Pi Foundation."),
    ("Replacing a bicycle inner tube", "ifixit",
     "Remove the wheel, lever off one bead, swap the tube, inflate a little, re-seat the tire."),
    ("Bowline knot", "wikipedia_en_all",
     "A fixed loop that holds under load and still unties easily afterwards."),
    ("Solar charging basics", "wikipedia_en_all",
     "Panel watts, controller type (PWM or MPPT) and battery chemistry set the charge rate."),
]
_AUDIT = [
    "2026-10-16T08:02:11+01:00\tsudo apt-get install -y mosh",
    "2026-10-16T08:05:40+01:00\tsystemctl --user status syncthing",
    "2026-10-16T08:06:02+01:00\tsudo nft list ruleset | head -40",
    "2026-10-16T09:14:55+01:00\tbtrfs subvolume list /",
    "2026-10-16T09:15:02+01:00\tsudo apt-get upgrade -y",
    "2026-10-16T09:20:31+01:00\tjournalctl -p err -b | tail -20",
]
_MHZ = {"performance": 2400, "balanced": 2000, "endurance": 1500}


class FakeBackend:
    """Plausible numbers that change a little on every refresh; mutable where the UI has buttons."""

    def __init__(self) -> None:
        self._tick = itertools.count()
        self.profile = "balanced"
        self.brightness = 60
        self.resolver_enabled = True
        self.snapshots = [
            {"name": "20261015-220000-first-nvme-boot", "created": "2026-10-15 22:00"},
            {"name": "20261016-091500-claude", "created": "2026-10-16 09:15"},
        ]

    def device_status(self) -> dict:
        n = next(self._tick)
        temp = 55.0 + n % 30  # climbs through the 70 and 80 C thresholds, then starts again
        return {
            "model": "Raspberry Pi 5 Model B Rev 1.0",
            "temp_c": temp,
            "throttled_hex": "0x80000" if temp >= 80 else "0x0",
            "throttle_flags": ["soft-temp-limit"] if temp >= 80 else [],
            "cpu_mhz": _MHZ[self.profile],
            "load": [0.42, 0.35, 0.30],
            "mem_total_mb": 4045,
            "mem_avail_mb": 2600 - (n % 6) * 40,
            "disks": [
                {"mount": "/", "total_gb": 1863.0, "used_gb": 312.6},
                {"mount": "/boot/firmware", "total_gb": 0.5, "used_gb": 0.07},
            ],
            "uptime_s": 3 * 86400 + 4 * 3600 + 12 * 60 + n * 5,
            "hostname": "pocket",
        }

    def power_status(self) -> dict:
        return {"source": "usb-c", "battery_pct": 87.0, "volts": 5.12, "amps": 1.41, "watts": 7.2,
                "rails": {"3v3": 3.30, "5v": 5.08, "1v8": 1.80}, "profile": self.profile}

    def net_status(self) -> dict:
        return {
            "interfaces": [
                {"name": "wlan0", "ip": "192.0.2.42", "state": "up"},
                {"name": "eth0", "ip": None, "state": "down"},
            ],
            "wifi": {"ssid": "ExampleNet", "signal": 72},
            "resolver_ok": self.resolver_enabled,
            "default_if": "wlan0",
        }

    def snapshot_list(self) -> list[dict]:
        return list(self.snapshots)

    def snapshot_create(self, label: str) -> dict:
        slug = "-".join(label.lower().split()) or "manual"
        minute = len(self.snapshots)
        name = f"20261016-12{minute:02d}00-{slug}"
        self.snapshots.append({"name": name, "created": f"2026-10-16 12:{minute:02d}"})
        return {"name": name, "ok": True, "message": f"snapshot {name} created"}

    def resolver_status(self) -> dict:
        if self.resolver_enabled:
            return {"enabled": True, "blocked_recent": 1234,
                    "detail": "blocky on 127.0.0.1:53, OISD big + HaGeZi Pro"}
        return {"enabled": False, "blocked_recent": None,
                "detail": "blocky stopped: queries go straight upstream"}

    def resolver_set(self, enabled: bool) -> dict:
        self.resolver_enabled = bool(enabled)
        return {"enabled": self.resolver_enabled, "ok": True}

    def kb_search(self, query: str, limit: int = 10) -> list[dict]:
        words = query.lower().split()
        scored = []
        for title, zim, snippet in _KB:
            text = f"{title} {snippet}".lower()
            score = sum(text.count(w) for w in words)
            if words and score:
                url = f"http://127.0.0.1:8090/{zim}/A/{title.replace(' ', '_')}"
                scored.append((-score, title, {"title": title, "url": url, "snippet": snippet}))
        return [hit for _, _, hit in sorted(scored)][:limit]

    def audit_tail(self, n: int = 20) -> list[str]:
        return _AUDIT[-n:]

    def set_power_profile(self, name: str) -> dict:
        if name not in _MHZ:
            return {"profile": self.profile, "ok": False, "message": f"unknown profile {name!r}"}
        self.profile = name
        return {"profile": name, "ok": True}

    def set_brightness(self, pct: int) -> dict:
        self.brightness = max(5, min(100, int(pct)))
        return {"pct": self.brightness, "ok": True}
