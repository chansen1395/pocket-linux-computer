"""pocket-helper is the only thing the device user may run as root, so its allow-list is tested hard.

The script has no .py extension (it is installed as /usr/local/bin/pocket-helper), so it is loaded by path.
Nothing here touches the system: only plan() and main() with a recording runner are used.
"""
import importlib.machinery
import importlib.util
import os
from pathlib import Path

import pytest

from pocket_core import linux

HELPER_PATH = Path(__file__).resolve().parents[2] / "provision" / "config" / "usr" / "local" / "bin" / "pocket-helper"


@pytest.fixture(scope="module")
def helper():
    loader = importlib.machinery.SourceFileLoader("pocket_helper", str(HELPER_PATH))
    spec = importlib.util.spec_from_loader("pocket_helper", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_accepted_requests_build_exact_steps(helper):
    assert helper.plan(["set-governor", "policy0", "powersave"]) == [
        ("write", "/sys/devices/system/cpu/cpufreq/policy0/scaling_governor", "powersave")]
    assert helper.plan(["set-max-freq", "policy4", "1500000"]) == [
        ("write", "/sys/devices/system/cpu/cpufreq/policy4/scaling_max_freq", "1500000")]
    assert helper.plan(["set-profile", "endurance"]) == [
        ("mkdir", "/var/lib/pocket"), ("write", "/var/lib/pocket/power-profile", "endurance\n")]
    assert helper.plan(["snapshot", "20261016-190718-pre-apt"]) == [
        ("run", ["/usr/bin/btrfs", "subvolume", "snapshot", "-r", "/", "/.snapshots/20261016-190718-pre-apt"])]
    assert helper.plan(["snapshot-delete", "20261016-190718-claude"]) == [
        ("run", ["/usr/bin/btrfs", "subvolume", "delete", "/.snapshots/20261016-190718-claude"])]


@pytest.mark.parametrize("argv", [
    [],
    ["unknown"],
    ["tee", "/etc/sudoers.d/x"],
    ["set-governor"],
    ["set-governor", "policy0"],
    ["set-governor", "policy0", "powersave", "extra"],
    # the attack a wildcard sudoers rule allows: a second path after the expected one
    ["set-governor", "policy0 /etc/sudoers.d/x", "powersave"],
    ["set-governor", "policy0/../../../../etc/sudoers.d/x", "powersave"],
    ["set-governor", "../policy0", "powersave"],
    ["set-governor", "policy0\n", "powersave"],
    ["set-governor", "policy", "powersave"],
    ["set-governor", "policy123", "powersave"],
    ["set-governor", "cpu0", "powersave"],
    ["set-governor", "policy0", "powersave /etc/passwd"],
    ["set-governor", "policy0", "userspace"],
    ["set-governor", "policy0", ""],
    ["set-max-freq", "policy0", "1500000 /etc/x"],
    ["set-max-freq", "policy0", "1500000\n"],
    ["set-max-freq", "policy0", "-1500000"],
    ["set-max-freq", "policy0", "99999"],
    ["set-max-freq", "policy0", "9999999"],
    ["set-max-freq", "policy0", "0x16e360"],
    ["set-max-freq", "policy0", "1500000.0"],
    ["set-max-freq", "policy0", "١٥٠٠٠٠٠"],  # Arabic-Indic digits
    ["set-profile", "turbo"],
    ["set-profile", "balanced extra"],
    ["set-profile", "../balanced"],
    ["set-profile"],
    ["snapshot", "/etc"],
    ["snapshot", "../../etc/x"],
    ["snapshot", "20261016-190718-a/b"],
    ["snapshot", "20261016-190718-a b"],
    ["snapshot", "20261016-190718-"],
    ["snapshot", "20261016-190718-" + "a" * 41],
    ["snapshot", "20261016-190718-pre\n"],
    ["snapshot", "-r"],
    ["snapshot", "20261016-190718-ok", "/tmp/x"],
    ["snapshot-delete", "20261016-190718-pre-apt"],      # only the hook's "-claude" snapshots may be deleted
    ["snapshot-delete", "20261016-190718-claude/../x"],
    ["snapshot-delete", "../.snapshots/20261016-190718-claude"],
    ["snapshot-delete", "/.snapshots/20261016-190718-claude"],
    ["snapshot-delete", "20261016-190718-claude\n"],
    ["snapshot-delete", "20261016-190718-claude-x"],
    ["snapshot-delete"],
])
def test_refused_requests(helper, argv):
    with pytest.raises(helper.Refused):
        helper.plan(argv)


def test_every_accepted_snapshot_name_stays_one_path_component(helper):
    label_chars = "abcXYZ019._-"
    for label in ("a", "..", "...", "-", "pre-apt_upgrade.v2", label_chars, "x" * 40):
        steps = helper.plan(["snapshot", f"20261016-190718-{label}"])
        target = steps[0][1][-1]
        assert os.path.dirname(target) == "/.snapshots" and "/" not in os.path.basename(target)


def test_main_returns_2_on_refusal_and_does_not_run(helper, capsys):
    ran = []
    assert helper.main(["set-governor", "policy0 /etc/sudoers.d/x", "powersave"], run=ran.append) == 2
    assert helper.main([], run=ran.append) == 2
    assert ran == []
    assert "refused" in capsys.readouterr().err


def test_main_runs_validated_steps_only_as_root(helper, monkeypatch):
    seen = []
    monkeypatch.setattr(helper, "is_root", lambda: False)
    assert helper.main(["set-profile", "balanced"], run=seen.append) == 2 and seen == []
    monkeypatch.setattr(helper, "is_root", lambda: True)
    assert helper.main(["set-profile", "balanced"], run=lambda steps: seen.append(steps) or 0) == 0
    assert seen == [[("mkdir", "/var/lib/pocket"), ("write", "/var/lib/pocket/power-profile", "balanced\n")]]


def test_execute_refuses_to_write_through_a_symlink(helper, tmp_path):
    target = tmp_path / "real"
    link = tmp_path / "link"
    target.write_text("keep")
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not available")
    with pytest.raises(OSError):
        helper.execute([("write", str(link), "x")])
    assert target.read_text() == "keep"


def test_backend_asks_the_helper_not_tee(monkeypatch):
    """When a direct write fails, the Linux backend must go through pocket-helper with exact arguments."""
    calls = []
    monkeypatch.setattr(linux, "run", lambda cmd, timeout=5, input=None: calls.append(cmd) or (0, "", ""))
    ok, err = linux.write_privileged("/nonexistent-dir/scaling_governor", "powersave",
                                     ["set-governor", "policy0", "powersave"])
    assert ok and err == ""
    assert calls == [["sudo", "-n", linux.HELPER, "set-governor", "policy0", "powersave"]]
    assert all("tee" not in part for cmd in calls for part in cmd)
    calls.clear()
    ok, err = linux.write_privileged("/nonexistent-dir/brightness", "50")  # no helper verb: direct write only
    assert not ok and "cannot write" in err and calls == []
