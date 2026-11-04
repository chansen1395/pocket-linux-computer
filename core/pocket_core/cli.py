"""`pocketctl`: the command line over the backend. Every command accepts --json for the raw result."""
from __future__ import annotations

import argparse
import json

from .backend import POWER_PROFILES, get_backend


def _rows(rows: list[tuple[str, object]]) -> str:
    width = max(len(k) for k, _ in rows)
    return "\n".join(f"{k:<{width}}  {v}" for k, v in rows)


def _num(v, unit: str = "", digits: int = 1) -> str:
    return "--" if v is None else f"{v:.{digits}f}{unit}"


def _uptime(seconds: int) -> str:
    days, rem = divmod(int(seconds or 0), 86400)
    hours, minutes = divmod(rem // 60, 60)
    return (f"{days}d " if days else "") + f"{hours}h {minutes:02d}m"


def fmt_device(d: dict) -> list[tuple[str, object]]:
    disks = "  ".join(f"{x['mount']} {x['used_gb']}/{x['total_gb']} GB" for x in d["disks"]) or "--"
    return [
        ("Device", f"{d['model']}  ({d['hostname']})"),
        ("Temp", f"{_num(d['temp_c'], ' C')}  throttled {d['throttled_hex']} ({', '.join(d['throttle_flags']) or 'ok'})"),
        ("CPU", f"{_num(d['cpu_mhz'], ' MHz', 0)}  load {' '.join(f'{x:.2f}' for x in d['load'])}"),
        ("Memory", f"{d['mem_avail_mb']} / {d['mem_total_mb']} MB available"),
        ("Disks", disks),
        ("Uptime", _uptime(d["uptime_s"])),
    ]


def fmt_power(p: dict) -> list[tuple[str, object]]:
    return [
        ("Power", f"{p['source']}  {_num(p['volts'], ' V', 2)}  {_num(p['amps'], ' A', 2)}  {_num(p['watts'], ' W')}"
                  f"  battery {_num(p['battery_pct'], '%', 0)}"),
        ("Profile", p["profile"]),
    ]


def fmt_net(n: dict) -> list[tuple[str, object]]:
    wifi = n["wifi"]
    return [
        ("Wi-Fi", f"{wifi['ssid']} ({wifi['signal']}%)" if wifi else "--"),
        ("Interfaces", "  ".join(f"{i['name']} {i['ip'] or '-'} {i['state']}" for i in n["interfaces"]) or "--"),
        ("DNS", f"resolver {'ok' if n['resolver_ok'] else 'FAILED'}  default via {n['default_if'] or '--'}"),
    ]


def status_summary(d: dict, p: dict, n: dict) -> str:
    """One line for the MCP resource and status bars."""
    wifi = f"wifi {n['wifi']['ssid']} {n['wifi']['signal']}%" if n["wifi"] else "no wifi"
    return (f"{d['model']} | {_num(d['temp_c'], ' C')} | throttled {d['throttled_hex']} | load {d['load'][0]:.2f} | "
            f"mem {d['mem_avail_mb']}/{d['mem_total_mb']} MB free | {p['source']} {_num(p['watts'], ' W')} | "
            f"profile {p['profile']} | {wifi} | dns {'ok' if n['resolver_ok'] else 'FAIL'}")


def cmd_status(b, a):
    d, p, n = b.device_status(), b.power_status(), b.net_status()
    return {"device": d, "power": p, "net": n}, _rows(fmt_device(d) + fmt_power(p) + fmt_net(n))


def cmd_power(b, a):
    if a.profile:
        r = b.set_power_profile(a.profile)
        return r, f"profile {r['profile']}: {r['message']}"
    p = b.power_status()
    rails = "  ".join(f"{k}={v}" for k, v in sorted(p["rails"].items())) or "--"
    return p, _rows(fmt_power(p) + [("Rails", rails)])


def cmd_net(b, a):
    n = b.net_status()
    return n, _rows(fmt_net(n))


def cmd_snapshot(b, a):
    if a.action == "create":
        r = b.snapshot_create(a.label)
        return r, r["message"]
    lst = b.snapshot_list()
    return lst, "\n".join(f"{s['created']}  {s['name']}" for s in lst) or "no snapshots"


def cmd_resolver(b, a):
    if a.action in ("on", "off"):
        r = b.resolver_set(a.action == "on")
        return r, f"blocking {'enabled' if r['enabled'] else 'disabled'}" + ("" if r["ok"] else f"  FAILED: {r.get('message', '')}")
    r = b.resolver_status()
    return r, _rows([("Blocking", "enabled" if r["enabled"] else "disabled"),
                     ("Blocked", _num(r["blocked_recent"], "", 0)), ("Detail", r["detail"])])


def cmd_kb(b, a):
    res = b.kb_search(" ".join(a.query), a.limit)
    return res, "\n\n".join(f"{r['title']}\n  {r['url']}\n  {r['snippet']}" for r in res) or "no results"


def cmd_audit(b, a):
    lines = b.audit_tail(a.n)
    return lines, "\n".join(lines) or "audit log empty"


def cmd_brightness(b, a):
    r = b.set_brightness(a.pct)
    return r, f"brightness {r['pct']}%" + ("" if r["ok"] else f"  FAILED: {r.get('message', '')}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pocketctl", description="Pocket device status and control")
    p.add_argument("--json", action="store_true", help="print the raw result as JSON")
    sub = p.add_subparsers(dest="command", required=True)

    def add(name, func, help):
        s = sub.add_parser(name, help=help)
        s.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="print the raw result as JSON")
        s.set_defaults(func=func)
        return s

    add("status", cmd_status, "device, power and network summary")
    add("power", cmd_power, "show power, or switch the power profile").add_argument("profile", nargs="?", choices=POWER_PROFILES)
    add("net", cmd_net, "network status")
    s = add("snapshot", cmd_snapshot, "list or create btrfs root snapshots")
    s.add_argument("action", choices=["list", "create"])
    s.add_argument("label", nargs="?", default="manual")
    add("resolver", cmd_resolver, "ad-blocking resolver: status, on, off").add_argument(
        "action", nargs="?", choices=["status", "on", "off"], default="status")
    s = add("kb", cmd_kb, "search the offline knowledge base (Kiwix)")
    s.add_argument("query", nargs="+")
    s.add_argument("-n", "--limit", type=int, default=10)
    add("audit", cmd_audit, "tail the Claude Code audit log").add_argument("-n", type=int, default=20)
    add("brightness", cmd_brightness, "set the display backlight (0-100)").add_argument("pct", type=int)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result, text = args.func(get_backend(), args)
    print(json.dumps(result, indent=2) if args.json else text)
    return 0 if not isinstance(result, dict) or result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
