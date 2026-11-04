"""Pure parsers for the Linux backend: no I/O, so each one is unit-testable on any machine."""
from __future__ import annotations

import json
import re
import struct
from html.parser import HTMLParser

THROTTLE_BITS = {
    0: "under-voltage now", 1: "arm frequency capped now", 2: "throttled now", 3: "soft temp limit now",
    16: "under-voltage occurred", 17: "arm frequency capped occurred", 18: "throttled occurred",
    19: "soft temp limit occurred",
}


def parse_throttled(text: str) -> tuple[str, list[str]]:
    """'throttled=0x50005' -> ('0x50005', [flag names for the set bits])."""
    bits = int(text.strip().rsplit("=", 1)[-1], 16)
    return hex(bits), [name for bit, name in THROTTLE_BITS.items() if bits & (1 << bit)]


def parse_pmic(text: str) -> tuple[dict[str, float], float | None]:
    """`vcgencmd pmic_read_adc` lines ('VDD_CORE_A current(7)=0.75000000A') -> ({rail: value}, watts).

    watts is the sum of current x voltage over rails that share a prefix (X_A with X_V), or None when
    no such pair exists. Rails are rounded to 4 decimals, watts to 2 (computed from the raw values).
    """
    raw: dict[str, float] = {}
    for line in text.splitlines():
        m = re.match(r"\s*(\S+)\s+\w+\(\d+\)=([0-9.+-]+)[AV]?\s*$", line)
        if m:
            raw[m.group(1)] = float(m.group(2))
    pairs = [(a, raw[n[:-2] + "_V"]) for n, a in raw.items() if n.endswith("_A") and n[:-2] + "_V" in raw]
    watts = round(sum(a * v for a, v in pairs), 2) if pairs else None
    return {k: round(v, 4) for k, v in raw.items()}, watts


def parse_meminfo(text: str) -> tuple[int, int]:
    """/proc/meminfo -> (MemTotal MB, MemAvailable MB)."""
    kb = {k: int(v.split()[0]) for k, _, v in (ln.partition(":") for ln in text.splitlines())
          if k in ("MemTotal", "MemAvailable")}
    return kb.get("MemTotal", 0) // 1024, kb.get("MemAvailable", 0) // 1024


def parse_ip_addr(text: str) -> list[dict]:
    """`ip -j addr` -> [{name, ip (first IPv4 or None), state}], loopback left out."""
    out = []
    for iface in json.loads(text or "[]"):
        if iface.get("ifname") == "lo":
            continue
        ip = next((a.get("local") for a in iface.get("addr_info", []) if a.get("family") == "inet"), None)
        out.append({"name": iface.get("ifname", "?"), "ip": ip, "state": str(iface.get("operstate", "unknown")).lower()})
    return out


def parse_default_route(text: str) -> str | None:
    """`ip -j route show default` -> device of the first default route."""
    routes = json.loads(text or "[]")
    return routes[0].get("dev") if routes else None


def parse_nmcli_wifi(text: str) -> dict | None:
    """`nmcli -t -f ACTIVE,SSID,SIGNAL dev wifi` rows ('yes:ExampleNet:71'); a ':' in an SSID arrives as '\\:'."""
    for line in text.splitlines():
        m = re.match(r"yes:(.*):(\d+)$", line.strip())
        if m:
            return {"ssid": m.group(1).replace("\\:", ":"), "signal": int(m.group(2))}
    return None


class _KiwixResults(HTMLParser):
    """Collects title/href/snippet from the <li> items inside kiwix-serve's <div class="results">."""

    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict] = []
        self._div_depth = 0             # > 0 while inside <div class="results">
        self._item: dict | None = None
        self._field: str | None = None  # which key of _item receives text

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div" and (self._div_depth or "results" in (a.get("class") or "").split()):
            self._div_depth += 1
        elif tag == "li" and self._div_depth:
            self._item = {"title": "", "url": "", "snippet": ""}
        elif tag == "a" and self._item is not None and not self._item["url"]:
            self._item["url"] = a.get("href") or ""
            self._field = "title"
        elif tag == "cite" and self._item is not None:
            self._field = "snippet"

    def handle_endtag(self, tag):
        if tag == "div" and self._div_depth:
            self._div_depth -= 1
        elif tag in ("a", "cite"):
            self._field = None
        elif tag == "li" and self._item is not None:
            if self._item["title"]:
                self.results.append({k: " ".join(v.split()) for k, v in self._item.items()})
            self._item = None

    def handle_data(self, data):
        if self._item is not None and self._field:
            self._item[self._field] += data


def parse_kiwix(html: str, base: str = "") -> list[dict]:
    """kiwix-serve /search HTML -> [{title, url, snippet}]; relative hrefs are prefixed with base."""
    p = _KiwixResults()
    p.feed(html)
    for r in p.results:
        if r["url"].startswith("/"):
            r["url"] = base + r["url"]
    return p.results


def dns_build_query(name: str, qid: int, qtype: int = 1) -> bytes:
    """A minimal DNS query: header (recursion desired), one question, class IN."""
    labels = b"".join(bytes([len(part)]) + part.encode("ascii") for part in name.strip(".").split("."))
    return struct.pack("!HHHHHH", qid, 0x0100, 1, 0, 0, 0) + labels + b"\x00" + struct.pack("!HH", qtype, 1)


def _skip_name(data: bytes, pos: int) -> int:
    while True:
        length = data[pos]
        if length == 0:
            return pos + 1
        if length & 0xC0 == 0xC0:  # compression pointer ends the name
            return pos + 2
        pos += 1 + length


def dns_parse_response(data: bytes) -> dict:
    """DNS response -> {id, rcode, answers: [A record IPs]}. Raises on a malformed packet."""
    qid, flags, qd, an, _, _ = struct.unpack("!HHHHHH", data[:12])
    pos = 12
    for _ in range(qd):
        pos = _skip_name(data, pos) + 4
    answers = []
    for _ in range(an):
        pos = _skip_name(data, pos)
        rtype, _, _, rdlen = struct.unpack("!HHIH", data[pos:pos + 10])
        pos += 10
        if rtype == 1 and rdlen == 4:
            answers.append(".".join(str(b) for b in data[pos:pos + 4]))
        pos += rdlen
    return {"id": qid, "rcode": flags & 0xF, "answers": answers}
