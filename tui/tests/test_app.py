"""Pocket TUI tests: the fake backend, a dry-run runner that only records commands, and Textual's
headless pilot. No network, no subprocesses, no pocket_core."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from textual.widgets import Input, ListView, TabbedContent

from pocket_tui.app import ConfirmScreen, PocketTui, PromptScreen, render_once
from pocket_tui.backend_fake import FakeBackend
from pocket_tui.runner import Runner


@pytest.fixture
def parts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[PocketTui, FakeBackend, Runner]:
    monkeypatch.setenv("EDITOR", "nano")
    backend, runner = FakeBackend(), Runner(dry_run=True)
    app = PocketTui(backend=backend, runner=runner, backend_name="test", notes_dir=tmp_path / "notes")
    return app, backend, runner


async def settle(app: PocketTui, pilot) -> None:
    """Let queued messages, thread workers and the callbacks they schedule all finish."""
    for _ in range(3):
        await pilot.pause()
        await app.workers.wait_for_complete()


async def test_mounts_and_shows_fake_status(parts):
    app, _, _ = parts
    async with app.run_test() as pilot:
        await settle(app, pilot)
        text = app.export_text()
        assert "pocket" in text
        assert re.search(r"Temp \d\d\.\d .C", text)
        assert "ExampleNet" in text and "Resolver OK" in text
        assert app.notes_dir.is_dir()


async def test_number_keys_switch_tabs(parts):
    app, _, _ = parts
    async with app.run_test() as pilot:
        await settle(app, pilot)
        tabs = app.query_one(TabbedContent)
        for key, name in zip("23451", ("data", "radio", "ai", "sys", "stat")):
            await pilot.press(key)
            await pilot.pause()
            assert tabs.active == name


async def test_data_search_and_open(parts):
    app, backend, runner = parts
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("2", "/", *"first aid", "enter")
        await settle(app, pilot)
        expected = [hit["url"] for hit in backend.kb_search("first aid")]
        assert expected and [row.payload for row in app.query("#kb-results Entry")] == expected
        results = app.query_one("#kb-results", ListView)
        results.focus()
        results.index = 0
        await pilot.press("enter")
        await pilot.pause()
        assert runner.history[-1][-1] == expected[0]


async def test_new_note_is_written_and_opened(parts):
    app, _, runner = parts
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("2", "n")
        await settle(app, pilot)
        notes = list(app.notes_dir.glob("*.md"))
        assert len(notes) == 1 and notes[0].read_text(encoding="utf-8").startswith("# ")
        assert runner.history[-1] == ["nano", str(notes[0])]
        assert len(app.query("#notes-list Entry")) == 1


async def test_sys_snapshot_adds_one(parts):
    app, backend, _ = parts
    async with app.run_test() as pilot:
        await settle(app, pilot)
        before = len(backend.snapshot_list())
        await pilot.press("5", "s")
        await pilot.pause()
        assert isinstance(app.screen, PromptScreen)
        await pilot.press(*"before upgrade", "enter")
        await settle(app, pilot)
        assert len(backend.snapshot_list()) == before + 1
        assert backend.snapshot_list()[-1]["name"].endswith("-before-upgrade")
        assert len(app.query("#snap-list Entry")) == before + 1


async def test_resolver_toggle_flips_state(parts):
    app, backend, _ = parts
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("5")
        assert backend.resolver_status()["enabled"] is True
        await pilot.press("t")
        await settle(app, pilot)
        assert backend.resolver_status()["enabled"] is False
        assert "Ad blocking OFF" in app.export_text()
        await pilot.press("t")
        await settle(app, pilot)
        assert backend.resolver_status()["enabled"] is True


async def test_brightness_and_profile_reach_backend(parts):
    app, backend, _ = parts
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("5", "-")
        await settle(app, pilot)
        assert backend.brightness == 50
        await pilot.press("=")
        await settle(app, pilot)
        assert backend.brightness == 60
        await pilot.press("1", "p")
        await settle(app, pilot)
        assert backend.profile == "endurance"


async def test_radio_play_and_stop_only_record_commands(parts):
    app, _, runner = parts
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("3")
        app.query_one("#media-target", Input).value = "noaa weather radio"
        await pilot.press("a")
        await pilot.pause()
        argv = runner.history[-1]
        assert argv[0] == "mpv" and "--no-video" in argv and argv[-1] == "ytdl://ytsearch1:noaa weather radio"
        app.query_one("#media-target", Input).value = "https://example.org/talk"
        await pilot.press("v")
        await pilot.pause()
        assert runner.history[-1][-1] == "https://example.org/talk" and "--no-video" not in runner.history[-1]
        await pilot.press("x")
        await pilot.pause()
        assert app.media_proc is None


async def test_ai_claude_runs_in_terminal_and_sys_confirm(parts):
    app, _, runner = parts
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("4", "c")
        await pilot.pause()
        assert Path(runner.history[-1][0]).stem == "claude"
        assert app.header.ai_active is False  # cleared once the session ends
        await pilot.press("5", "b")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmScreen)
        await pilot.press("n")
        await pilot.pause()
        assert runner.history[-1][0] != "sudo"
        await pilot.press("h", "y")
        await pilot.pause()
        assert runner.history[-1] == ["sudo", "-n", "systemctl", "poweroff"]


async def test_keys_are_scoped_to_their_tab(parts):
    app, backend, _ = parts
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("t")  # resolver toggle belongs to SYS; on STAT it must do nothing
        await settle(app, pilot)
        assert backend.resolver_status()["enabled"] is True


@pytest.mark.parametrize("size", [(80, 24), (160, 45)])
async def test_render_once_at_both_sizes(parts, size):
    app, _, _ = parts
    text = await render_once(app, size)
    lines = [line for line in text.splitlines() if line.strip()]
    assert "1 STAT" in text and "5 SYS" in text and "q Quit" in text
    assert "DEVICE" in text and "NETWORK" in text and "pocket" in text
    assert max(len(line) for line in lines) <= size[0]
    assert len(text.splitlines()) <= size[1]

