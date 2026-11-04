"""The fake backend: shapes, determinism and setter round trips."""
from pocket_core.backend import get_backend
from pocket_core.fake import FakeBackend


def test_get_backend_fake(monkeypatch):
    monkeypatch.setenv("POCKET_BACKEND", "fake")
    assert isinstance(get_backend(), FakeBackend)


def test_shapes():
    b = FakeBackend()
    d = b.device_status()
    assert d["model"].startswith("Raspberry Pi 5") and d["temp_c"] == 48.2 and d["throttled_hex"] == "0x0"
    assert len(d["load"]) == 3 and len(d["disks"]) == 2 and d["mem_total_mb"] == 4045
    p = b.power_status()
    assert p["source"] == "usb-c" and p["profile"] == "balanced" and "EXT5V_V" in p["rails"]
    n = b.net_status()
    assert n["wifi"] == {"ssid": "ExampleNet", "signal": 71} and n["resolver_ok"]
    assert [i["ip"] for i in n["interfaces"]] == [None, "192.0.2.42"]
    assert len(b.snapshot_list()) == 5
    assert len(b.kb_search("raspberry pi")) == 3 and len(b.kb_search("x", limit=2)) == 2
    assert set(b.kb_search("first aid")[0]) == {"title", "url", "snippet"}
    assert len(b.audit_tail(3)) == 3 and b.audit_tail(0) == [] and len(b.audit_tail()) == 6


def test_setters_round_trip():
    b = FakeBackend()
    r = b.set_power_profile("endurance")
    assert r["ok"] and r["profile"] == "endurance" and b.power_status()["profile"] == "endurance"
    r = b.set_power_profile("turbo")
    assert not r["ok"] and "turbo" in r["message"] and b.power_status()["profile"] == "endurance"
    r = b.set_brightness(35)
    assert r["ok"] and r["pct"] == 35 and b.brightness == 35
    assert b.set_brightness(250)["pct"] == 100 and b.set_brightness(-5)["pct"] == 0
    r = b.resolver_set(False)
    assert r["ok"] and r["enabled"] is False and not b.resolver_status()["enabled"]
    assert b.resolver_set(True)["enabled"] and b.resolver_status()["enabled"]
    before = len(b.snapshot_list())
    r = b.snapshot_create("pre apt/upgrade!")
    assert r["ok"] and r["name"].endswith("-pre-apt-upgrade")
    assert len(b.snapshot_list()) == before + 1 and b.snapshot_list()[-1]["name"] == r["name"]

