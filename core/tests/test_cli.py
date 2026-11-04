"""Every CLI command runs against the fake backend, with and without --json."""
import json

import pytest

from pocket_core import cli
from pocket_core.fake import FakeBackend

CASES = [
    ["status"], ["power"], ["power", "endurance"], ["net"], ["snapshot", "list"], ["snapshot", "create", "test"],
    ["resolver"], ["resolver", "status"], ["resolver", "off"], ["resolver", "on"], ["kb", "raspberry", "pi"],
    ["kb", "-n", "1", "first", "aid"], ["audit"], ["audit", "-n", "2"], ["brightness", "40"],
]


@pytest.fixture(autouse=True)
def fake_backend(monkeypatch):
    monkeypatch.setenv("POCKET_BACKEND", "fake")


@pytest.mark.parametrize("argv", CASES, ids=" ".join)
def test_command_runs_and_json_parses(argv, capsys):
    assert cli.main(argv) == 0
    assert capsys.readouterr().out.strip()
    assert cli.main(argv + ["--json"]) == 0
    assert json.loads(capsys.readouterr().out) is not None


def test_json_flag_before_command(capsys):
    assert cli.main(["--json", "status"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert set(data) == {"device", "power", "net"} and data["device"]["temp_c"] == 48.2


def test_pretty_status_mentions_everything(capsys):
    cli.main(["status"])
    out = capsys.readouterr().out
    assert "Raspberry Pi 5" in out and "ExampleNet" in out and "192.0.2.42" in out and "balanced" in out


def test_exit_code_on_failure(monkeypatch, capsys):
    class Failing(FakeBackend):
        def set_brightness(self, pct):
            return {"pct": pct, "ok": False, "message": "no backlight"}

    monkeypatch.setattr(cli, "get_backend", Failing)
    assert cli.main(["brightness", "50"]) == 1
    assert "FAILED: no backlight" in capsys.readouterr().out
    assert cli.main(["brightness", "50", "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False


def test_bad_arguments_exit_nonzero():
    with pytest.raises(SystemExit) as e:
        cli.main(["power", "turbo"])
    assert e.value.code != 0
