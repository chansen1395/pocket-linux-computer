"""Backend for a Raspberry Pi on Raspberry Pi OS.

Every read is best-effort: a source that is missing or unreadable degrades to None, and an action
that fails reports ok=False with a message. Nothing here raises.
"""
from __future__ import annotations

import glob
import json
import os
import random
import shutil
import socket
import subprocess
from collections import deque
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

from . import parsers as P
from .backend import POWER_PROFILES, snapshot_name

SNAPSHOT_DIR = os.environ.get("POCKET_SNAPSHOT_DIR", "/.snapshots")
PROFILE_FILE = os.environ.get("POCKET_PROFILE_FILE", "/var/lib/pocket/power-profile")
BLOCKY_URL = os.environ.get("POCKET_BLOCKY_URL", "http://127.0.0.1:4000")
KIWIX_URL = os.environ.get("POCKET_KIWIX_URL", "http://127.0.0.1:8090")
HELPER = os.environ.get("POCKET_HELPER", "/usr/local/bin/pocket-helper")
AUDIT_LOG = Path(os.environ.get("POCKET_AUDIT_LOG", "~/.pocket/audit.log")).expanduser()
DISK_MOUNTS = ("/", "/home", "/data", "/boot/firmware")
CPUFREQ_POLICIES = "/sys/devices/system/cpu/cpufreq/policy[0-9]*"
GOVERNORS = {"performance": ["performance"], "balanced": ["ondemand", "schedutil", "conservative"],
             "endurance": ["powersave", "conservative", "schedutil"]}
ENDURANCE_MAX_KHZ = "1500000"


def safe(fn, default=None):
    """Evaluate fn(); any exception becomes the default."""
    try:
        return fn()
    except Exception:
        return default


def read_text(path: str) -> str | None:
    return safe(lambda: Path(path).read_text(errors="replace"))


def run(cmd: list[str], timeout: float = 5, input: str | None = None) -> tuple[int, str, str]:
    """(returncode, stdout, stderr); a missing binary or a timeout looks like a failed exit."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, input=input)
        return p.returncode, p.stdout, p.stderr.strip()
    except (OSError, subprocess.SubprocessError) as e:
        return 127, "", str(e)


def output(cmd: list[str], timeout: float = 5) -> str | None:
    rc, out, _ = run(cmd, timeout)
    return out if rc == 0 else None


def helper(*args: str, timeout: float = 60) -> tuple[int, str, str]:
    """Run pocket-helper through `sudo -n`. The helper checks its arguments against an exact allow-list."""
    return run(["sudo", "-n", HELPER, *args], timeout=timeout)


def write_privileged(path: str, content: str, helper_args: list[str] | None = None) -> tuple[bool, str]:
    """Write directly when permitted, else ask pocket-helper to do it (when helper_args is given)."""
    try:
        Path(path).write_text(content)
        return True, ""
    except OSError as exc:
        if helper_args is None:
            return False, f"cannot write {path} ({exc.strerror or exc})"
    rc, _, err = helper(*helper_args)
    return (True, "") if rc == 0 else (False, f"cannot write {path} ({err or 'pocket-helper failed'})")


def http_get(url: str, timeout: float = 3) -> str | None:
    """Body as text, or None on any failure (connection refused, HTTP error, timeout)."""
    try:
        with urlopen(url, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return None


def dns_query(name: str, server: str = "127.0.0.1", port: int = 53, timeout: float = 2.0) -> dict | None:
    """One UDP A query; the parsed response, or None when nothing valid comes back in time."""
    qid = random.randrange(1, 0xFFFF)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(timeout)
            s.sendto(P.dns_build_query(name, qid), (server, port))
            resp = P.dns_parse_response(s.recvfrom(512)[0])
        return resp if resp["id"] == qid else None
    except Exception:
        return None


def root_fstype() -> str | None:
    for line in (read_text("/proc/mounts") or "").splitlines():
        parts = line.split()
        if len(parts) > 2 and parts[1] == "/":
            return parts[2]
    return None


class LinuxBackend:
    disable_duration = "15m"  # resolver_set(False) pauses blocking for this long; Blocky re-enables itself

    def device_status(self) -> dict:
        thr = output(["vcgencmd", "get_throttled"])
        throttled_hex, flags = safe(lambda: P.parse_throttled(thr), ("unknown", []))
        mem_total, mem_avail = safe(lambda: P.parse_meminfo(read_text("/proc/meminfo")), (0, 0))
        return {
            "model": (read_text("/proc/device-tree/model") or "unknown").strip("\x00\n "),
            "temp_c": safe(lambda: round(int(read_text("/sys/class/thermal/thermal_zone0/temp")) / 1000, 1)),
            "throttled_hex": throttled_hex, "throttle_flags": flags,
            "cpu_mhz": safe(lambda: int(read_text("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")) // 1000),
            "load": safe(lambda: [float(x) for x in read_text("/proc/loadavg").split()[:3]], [0.0, 0.0, 0.0]),
            "mem_total_mb": mem_total, "mem_avail_mb": mem_avail,
            "disks": self._disks(),
            "uptime_s": safe(lambda: int(float(read_text("/proc/uptime").split()[0])), 0),
            "hostname": socket.gethostname(),
        }

    @staticmethod
    def _disks() -> list[dict]:
        mounted = {ln.split()[1] for ln in (read_text("/proc/mounts") or "").splitlines() if len(ln.split()) > 1}
        disks = []
        for mount in DISK_MOUNTS:
            u = safe(lambda: shutil.disk_usage(mount)) if mount in mounted else None
            if u:
                disks.append({"mount": mount, "total_gb": round(u.total / 2**30, 1), "used_gb": round(u.used / 2**30, 1)})
        return disks

    def power_status(self) -> dict:
        pmic = output(["vcgencmd", "pmic_read_adc"])
        rails, watts = safe(lambda: P.parse_pmic(pmic), ({}, None))
        volts = rails.get("EXT5V_V")
        source, pct = ("usb-c" if pmic else "unknown"), None
        for cap in glob.glob("/sys/class/power_supply/*/capacity"):
            pct = safe(lambda: float(read_text(cap)))
            status = (read_text(os.path.join(os.path.dirname(cap), "status")) or "").strip().lower()
            source = "battery" if status == "discharging" else "usb-c"
            break
        # What the firmware negotiated with the supply (5000 on the 27 W PD supply, 900 on a plain charger).
        # A 3 A-class charger cut power under llama-bench on 2026-10-16, so this is worth surfacing.
        supply_ma = safe(lambda: int.from_bytes(
            open("/proc/device-tree/chosen/power/max_current", "rb").read()[:4], "big"))
        return {"source": source, "battery_pct": pct, "volts": volts,
                "amps": round(watts / volts, 2) if watts and volts else None,  # estimated input current
                "watts": watts, "rails": rails, "profile": self._profile(),
                "supply_max_ma": supply_ma}

    @staticmethod
    def _profile() -> str:
        return (read_text(PROFILE_FILE) or "").strip() or "balanced"

    def net_status(self) -> dict:
        wifi_cmd = ["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL", "dev", "wifi", "list", "--rescan", "no"]
        resp = dns_query("debian.org")
        return {
            "interfaces": safe(lambda: P.parse_ip_addr(output(["ip", "-j", "addr"])), []),
            "wifi": safe(lambda: P.parse_nmcli_wifi(output(wifi_cmd))),
            "resolver_ok": bool(resp and resp["rcode"] == 0),
            "default_if": safe(lambda: P.parse_default_route(output(["ip", "-j", "route", "show", "default"]))),
        }

    def snapshot_list(self) -> list[dict]:
        out = []
        for p in sorted(safe(lambda: [x for x in Path(SNAPSHOT_DIR).iterdir() if x.is_dir()], [])):
            created = safe(lambda: datetime.strptime(p.name[:15], "%Y%m%d-%H%M%S").isoformat()) \
                or safe(lambda: datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"), "")
            out.append({"name": p.name, "created": created})
        return out

    def snapshot_create(self, label: str) -> dict:
        name = snapshot_name(label, datetime.now())
        if root_fstype() != "btrfs":
            return {"name": name, "ok": False, "message": "root is not btrfs"}
        target = f"{SNAPSHOT_DIR}/{name}"
        rc, _, err = helper("snapshot", name)
        return {"name": name, "ok": rc == 0, "message": f"created {target}" if rc == 0 else (err or f"btrfs exited {rc}")}

    def resolver_status(self) -> dict:
        st = safe(lambda: json.loads(http_get(f"{BLOCKY_URL}/api/blocking/status")))
        if not isinstance(st, dict):
            return {"enabled": False, "blocked_recent": None, "detail": f"Blocky API not reachable at {BLOCKY_URL}"}
        enabled, secs = bool(st.get("enabled")), st.get("autoEnableInSec") or 0
        detail = "blocking enabled" if enabled else "blocking disabled" + (f", re-enables in {secs} s" if secs else "")
        return {"enabled": enabled, "blocked_recent": self._blocked_total(), "detail": detail}

    @staticmethod
    def _blocked_total() -> int | None:
        """Blocked responses since Blocky started, from its Prometheus endpoint when that is enabled."""
        lines = (http_get(f"{BLOCKY_URL}/metrics", timeout=2) or "").splitlines()
        hits = [float(ln.rsplit(" ", 1)[1]) for ln in lines
                if ln.startswith("blocky_response_total{") and 'response_type="BLOCKED"' in ln]
        return int(sum(hits)) if hits else None

    def resolver_set(self, enabled: bool) -> dict:
        path = "enable" if enabled else f"disable?duration={self.disable_duration}"
        reached = http_get(f"{BLOCKY_URL}/api/blocking/{path}") is not None
        now = self.resolver_status()
        return {"enabled": now["enabled"], "ok": reached and now["enabled"] == bool(enabled), "message": now["detail"]}

    def kb_search(self, query: str, limit: int = 10) -> list[dict]:
        q = quote(" ".join(query.split()))
        if not q:
            return []
        size = max(1, min(int(limit), 50))
        for url in (f"{KIWIX_URL}/search?pattern={q}&books.filter.lang=eng&pageLength={size}",
                    f"{KIWIX_URL}/search?pattern={q}&pageLength={size}"):
            html = http_get(url, timeout=10)
            results = safe(lambda: P.parse_kiwix(html, KIWIX_URL), []) if html else []
            if results:
                return results[:size]
        return []

    def audit_tail(self, n: int = 20) -> list[str]:
        if n <= 0:
            return []
        try:
            with AUDIT_LOG.open(errors="replace") as f:
                return [line.rstrip("\n") for line in deque(f, maxlen=n)]
        except OSError:
            return []

    def set_power_profile(self, name: str) -> dict:
        if name not in POWER_PROFILES:
            return {"profile": self._profile(), "ok": False,
                    "message": f"unknown profile {name!r}; use one of {', '.join(POWER_PROFILES)}"}
        problems = []
        ok, err = write_privileged(PROFILE_FILE, name + "\n", ["set-profile", name])
        problems += [] if ok else [err]
        policies = sorted(glob.glob(CPUFREQ_POLICIES))
        problems += [] if policies else ["no cpufreq policy in sysfs (not a Pi?)"]
        for pol in policies:
            available = (read_text(f"{pol}/scaling_available_governors") or "").split()
            gov = next((g for g in GOVERNORS[name] if g in available), None)
            policy = os.path.basename(pol)
            ok, err = (write_privileged(f"{pol}/scaling_governor", gov, ["set-governor", policy, gov]) if gov
                       else (False, f"no {name} governor in {pol}"))
            problems += [] if ok else [err]
            max_khz = ENDURANCE_MAX_KHZ if name == "endurance" else (read_text(f"{pol}/cpuinfo_max_freq") or "").strip()
            ok, err = (write_privileged(f"{pol}/scaling_max_freq", max_khz, ["set-max-freq", policy, max_khz])
                       if max_khz else (True, ""))
            problems += [] if ok else [err]
        problems = list(dict.fromkeys(problems))
        return {"profile": name, "ok": not problems, "message": "; ".join(problems) or f"profile {name} applied"}

    def set_brightness(self, pct: int) -> dict:
        pct = max(0, min(100, int(pct)))
        problems = []
        if shutil.which("brightnessctl"):
            rc, _, err = run(["brightnessctl", "-q", "set", f"{pct}%"])
            if rc == 0:
                return {"pct": pct, "ok": True, "message": "set via brightnessctl"}
            problems.append(err or "brightnessctl failed")
        backlights = glob.glob("/sys/class/backlight/*")
        for bl in backlights:
            max_raw = safe(lambda: int(read_text(f"{bl}/max_brightness")), 255)
            ok, err = write_privileged(f"{bl}/brightness", str(round(max_raw * pct / 100)))
            if ok:
                return {"pct": pct, "ok": True, "message": f"set via {bl}"}
            problems.append(err)
        problems += [] if backlights else ["no /sys/class/backlight device"]
        return {"pct": pct, "ok": False, "message": "; ".join(problems)}
