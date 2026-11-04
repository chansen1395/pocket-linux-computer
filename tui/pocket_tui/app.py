"""Pocket TUI: a phosphor-green Textual UI for the device console mode.

One-line header, five tabs (STAT, DATA, RADIO, AI, SYS), a footer listing the keys that work
on the current tab. The App owns the backend, the command runner and every action; the panes
only compose widgets and show data.
"""

from __future__ import annotations

import io
import os
import shlex
import shutil
import subprocess
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterator

from rich.console import Console
from textual import on, work
from textual.app import App, ComposeResult, ScreenStackError, SuspendNotSupported
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.events import Resize
from textual.markup import escape
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.theme import Theme
from textual.widgets import (Button, Footer, Input, Label, ListItem, ListView, Log, Static,
                             TabbedContent, TabPane)

from .backend import Backend, load_backend
from .runner import Runner, RunnerError

TABS = {"stat": "1 STAT", "data": "2 DATA", "radio": "3 RADIO", "ai": "4 AI", "sys": "5 SYS"}
PROFILES = ("performance", "balanced", "endurance")
REFRESH_S = 5.0
NARROW_BELOW = 120  # columns; under this the STAT grid drops from three columns to two
BAR_FULL, BAR_EMPTY, DEG = "█", "░", "°"

PHOSPHOR = Theme(
    name="phosphor",
    primary="#2bff6a",
    secondary="#1f9d4a",
    accent="#9cff9c",
    warning="#ffb000",
    error="#ff4d2e",
    success="#2bff6a",
    foreground="#9cff9c",
    background="#050a05",
    surface="#0a140a",
    panel="#0f1f0f",
    dark=True,
    variables={
        "footer-background": "#0f1f0f",
        "footer-key-foreground": "#ffb000",
        "footer-description-foreground": "#9cff9c",
        "block-cursor-background": "#1f9d4a",
        "block-cursor-foreground": "#050a05",
    },
)


# --- small helpers -------------------------------------------------------------------------

def bar(frac: float, width: int = 14) -> str:
    """A text gauge: full blocks for the used part, light shade for the rest."""
    n = round(max(0.0, min(1.0, frac)) * width)
    return BAR_FULL * n + BAR_EMPTY * (width - n)


def gb(value: float) -> str:
    return f"{value:.1f}" if value < 10 else f"{value:.0f}"


def fmt_uptime(seconds: int) -> str:
    days, rest = divmod(int(seconds), 86400)
    hours, rest = divmod(rest, 3600)
    clock = f"{hours:02d}:{rest // 60:02d}"
    return f"{days}d {clock}" if days else clock


def temp_markup(temp: float | None) -> str:
    """Temperature with the 70/80 C thresholds: green, amber, red."""
    if temp is None:
        return "--"
    color = "$success" if temp < 70 else "$warning" if temp < 80 else "$error"
    return f"[bold {color}]{temp:.1f} {DEG}C[/]"


class Box(Vertical):
    """A bordered, titled monospace panel."""

    def __init__(self, title: str, *children: Any, id: str | None = None, classes: str = "") -> None:
        super().__init__(*children, id=id, classes=f"box {classes}".strip())
        self.border_title = title


class Entry(ListItem):
    """A list row that remembers what it stands for (a URL, a path, a snapshot name)."""

    def __init__(self, text: str, payload: Any) -> None:
        super().__init__(Label(text))
        self.payload = payload


def fill(list_view: ListView, entries: list[Entry], empty: str = "nothing here") -> None:
    list_view.clear()
    list_view.extend(entries or [ListItem(Label(empty))])


# --- header ----------------------------------------------------------------------------------

class PocketHeader(Horizontal):
    """Hostname, clock, power source, Wi-Fi, and an AI indicator that blinks while Claude runs."""

    ai_active = reactive(False)

    def compose(self) -> ComposeResult:
        yield Static("POCKET", id="hd-host")
        yield Static("", id="hd-clock")
        yield Static("", id="hd-power")
        yield Static("", id="hd-wifi")
        yield Static(" AI ", id="hd-ai")

    def on_mount(self) -> None:
        self.set_interval(1, self.tick)
        self.set_interval(0.5, self.blink)
        self.tick()

    def tick(self) -> None:
        self.query_one("#hd-clock", Static).update(datetime.now().strftime("%a %d %b  %H:%M:%S"))

    def blink(self) -> None:
        indicator = self.query_one("#hd-ai")
        indicator.set_class(self.ai_active and not indicator.has_class("on"), "on")

    def watch_ai_active(self, active: bool) -> None:
        self.query_one("#hd-ai").set_class(active, "active")

    def show(self, host: str, power: dict, net: dict) -> None:
        pct = power.get("battery_pct")
        battery = f" {pct:.0f}%" if pct is not None else ""
        wifi = net.get("wifi")
        self.query_one("#hd-host", Static).update(escape(host))
        self.query_one("#hd-power", Static).update(f"{escape(power.get('source', '?'))}{battery}")
        self.query_one("#hd-wifi", Static).update(
            f"wifi {escape(wifi['ssid'])} {wifi['signal']}%" if wifi else "wifi off")


# --- tabs ------------------------------------------------------------------------------------

class StatPane(TabPane):
    def compose(self) -> ComposeResult:
        with VerticalScroll(), Container(id="stat-grid"):
            yield Box("DEVICE", Static(id="device-text"), id="device-box")
            yield Box("POWER", Static(id="power-text"),
                      Horizontal(*[Button(p.capitalize(), id=f"prof-{p}") for p in PROFILES], classes="row"))
            yield Box("NETWORK", Static(id="net-text"))

    def show(self, dev: dict, pwr: dict, net: dict) -> None:
        self.query_one("#device-text", Static).update(self.device_markup(dev))
        self.query_one("#power-text", Static).update(self.power_markup(pwr))
        self.query_one("#net-text", Static).update(self.net_markup(net))
        for name in PROFILES:
            self.query_one(f"#prof-{name}", Button).set_class(name == pwr.get("profile"), "selected")

    @staticmethod
    def device_markup(d: dict) -> str:
        flags = d.get("throttle_flags") or []
        total, avail = d.get("mem_total_mb") or 0, d.get("mem_avail_mb") or 0
        used = total - avail
        lines = [
            f"[bold]{escape(d.get('model', '?'))}[/]",
            f"up {fmt_uptime(d.get('uptime_s') or 0)}   host {escape(d.get('hostname', '?'))}",
            f"Temp {temp_markup(d.get('temp_c'))}   CPU {d.get('cpu_mhz') or '--'} MHz",
            "Load " + " ".join(f"{x:.2f}" for x in d.get("load") or []),
            (f"Throttle [bold $warning]{escape(', '.join(flags))}[/] {escape(d.get('throttled_hex', ''))}"
             if flags else "Throttle [bold $success]none[/]"),
            f"RAM   {bar(used / total if total else 0)} {used / 1024:.1f}/{total / 1024:.1f} GB",
        ]
        for disk in d.get("disks") or []:
            cap, use = disk["total_gb"], disk["used_gb"]
            lines.append(f"{escape(disk['mount'])[:5]:<5} {bar(use / cap if cap else 0)} {gb(use)}/{gb(cap)} GB")
        return "\n".join(lines)

    @staticmethod
    def power_markup(p: dict) -> str:
        def num(value: float | None, unit: str, digits: int = 2) -> str:
            return f"{value:.{digits}f} {unit}" if value is not None else f"-- {unit}"

        pct = p.get("battery_pct")
        rails = "  ".join(f"{escape(k)} {v:.2f}" for k, v in (p.get("rails") or {}).items())
        return "\n".join([
            f"Source [bold]{escape(p.get('source', 'unknown'))}[/]   "
            f"Battery {f'{pct:.0f} %' if pct is not None else '--'}",
            f"{num(p.get('volts'), 'V')}  {num(p.get('amps'), 'A')}  [bold]{num(p.get('watts'), 'W', 1)}[/]",
            f"Rails {rails or '--'}",
            f"Profile [bold]{escape(p.get('profile', '?'))}[/]",
        ])

    @staticmethod
    def net_markup(n: dict) -> str:
        lines = [f"{escape(i['name']):<10} {escape(i.get('ip') or '-'):<15} {escape(i.get('state', '?'))}"
                 for i in n.get("interfaces") or []]
        wifi = n.get("wifi")
        lines.append(f"Wi-Fi {escape(wifi['ssid'])} signal {wifi['signal']} %" if wifi else "Wi-Fi off")
        resolver = "[bold $success]OK[/]" if n.get("resolver_ok") else "[bold $error]FAIL[/]"
        lines.append(f"Resolver {resolver}   default via {escape(n.get('default_if') or '-')}")
        return "\n".join(lines)


class DataPane(TabPane):
    def compose(self) -> ComposeResult:
        with Container(id="data-grid"):
            yield Box("LIBRARY", Input(placeholder="search the offline library; Enter on a hit opens it",
                                       id="kb-query"), ListView(id="kb-results"), classes="fill")
            yield Box("NOTES  ~/notes", ListView(id="notes-list"),
                      Horizontal(Button("New note", id="note-new"), Button("Open", id="note-open"),
                                 classes="row"), classes="fill")

    def show_results(self, results: list[dict]) -> None:
        fill(self.query_one("#kb-results", ListView),
             [Entry(f"[bold]{escape(r['title'])}[/]\n{escape(r.get('snippet', ''))}", r["url"]) for r in results],
             "no matches")

    def show_notes(self, paths: list[Path]) -> None:
        fill(self.query_one("#notes-list", ListView), [Entry(escape(p.name), p) for p in paths],
             "no notes yet: press n")


class RadioPane(TabPane):
    def compose(self) -> ComposeResult:
        yield Box("WATCH / LISTEN",
                  Input(placeholder="URL, or search terms (plays the first match)", id="media-target"),
                  Horizontal(Button("Play audio", id="play-audio"), Button("Play video", id="play-video"),
                             Button("Stop", id="play-stop", variant="warning"), classes="row"),
                  Static("idle", id="media-status"))
        yield Box("RADIO", Static("SDR and Meshtastic arrive in phase 3 (docs/06-roadmap.md)."))
        yield Box("COMMAND LOG", Log(id="cmd-log"), classes="fill")

    def set_status(self, text: str) -> None:
        self.query_one("#media-status", Static).update(escape(text))


class AiPane(TabPane):
    def compose(self) -> ComposeResult:
        yield Box("ASSISTANTS",
                  Horizontal(Button("Claude", id="ai-claude"), Button("Local model", id="ai-local"), classes="row"),
                  Static("Claude Code takes over this terminal; the Pocket TUI comes back when it exits."))
        yield Box("AUDIT  ~/.pocket/audit.log", Log(id="audit-log"), classes="fill")

    def show_audit(self, lines: list[str]) -> None:
        log = self.query_one("#audit-log", Log)
        log.clear()
        log.write_lines([line.replace("\t", "  ") for line in lines] or ["(empty)"])


class SysPane(TabPane):
    def compose(self) -> ComposeResult:
        with Container(id="sys-grid"):
            yield Box("SNAPSHOTS", ListView(id="snap-list"),
                      Horizontal(Button("New snapshot", id="snap-new"), classes="row"), classes="fill")
            with Vertical():
                yield Box("RESOLVER", Static(id="resolver-text"),
                          Horizontal(Button("Toggle", id="resolver-toggle"), classes="row"))
                yield Box("BRIGHTNESS", Horizontal(Button("-", id="bright-down"), Static(id="bright-text"),
                                                Button("+", id="bright-up"), classes="row"))
                yield Box("POWER", Horizontal(Button("Desktop", id="sys-desktop"),
                                              Button("Reboot", id="sys-reboot", variant="warning"),
                                              Button("Power off", id="sys-poweroff", variant="error"),
                                              classes="row"))

    def show_snapshots(self, snaps: list[dict]) -> None:
        fill(self.query_one("#snap-list", ListView),
             [Entry(f"[bold]{escape(s['name'])}[/]\n  {escape(s.get('created', ''))}", s["name"]) for s in snaps],
             "no snapshots")

    def show_resolver(self, status: dict) -> None:
        enabled = bool(status.get("enabled"))
        state = "[bold $success]ON[/]" if enabled else "[bold $error]OFF[/]"
        blocked = status.get("blocked_recent")
        self.query_one("#resolver-text", Static).update(
            f"Ad blocking {state}   blocked {blocked if blocked is not None else '--'}\n"
            f"{escape(status.get('detail', ''))}")
        self.query_one("#resolver-toggle", Button).label = "Turn off" if enabled else "Turn on"

    def show_brightness(self, pct: int) -> None:
        self.query_one("#bright-text", Static).update(f"{bar(pct / 100, 8)} {pct:3d} %")


# --- dialogs ---------------------------------------------------------------------------------

class ConfirmScreen(ModalScreen[bool]):
    BINDINGS = [Binding("y", "answer(True)", "Yes"), Binding("n", "answer(False)", "No"),
                Binding("escape", "answer(False)", "Cancel", show=False)]

    def __init__(self, question: str) -> None:
        super().__init__()
        self.question = question

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label(self.question)
            with Horizontal(classes="row"):
                yield Button("Yes", id="yes", variant="warning")
                yield Button("No", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(event.button.id == "yes")

    def action_answer(self, value: bool) -> None:
        self.dismiss(value)


class PromptScreen(ModalScreen[str | None]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, prompt: str, placeholder: str = "") -> None:
        super().__init__()
        self.prompt, self.placeholder = prompt, placeholder

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Label(self.prompt)
            yield Input(placeholder=self.placeholder, id="prompt-input")
            with Horizontal(classes="row"):
                yield Button("OK", id="ok")
                yield Button("Cancel", id="cancel")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self.dismiss(event.value.strip())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self.dismiss(self.query_one(Input).value.strip() if event.button.id == "ok" else None)

    def action_cancel(self) -> None:
        self.dismiss(None)


# --- the app ---------------------------------------------------------------------------------

class PocketTui(App[None]):
    CSS_PATH = "pocket_tui.tcss"
    TITLE = "Pocket TUI"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        *[Binding(key, f"switch_tab('{name}')", label, show=False)
          for key, (name, label) in zip("12345", TABS.items())],
        Binding("escape", "defocus", "Back", show=False),
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("p", "cycle_profile", "Profile"),
        Binding("slash", "focus_search", "Search", key_display="/"),
        Binding("n", "note_new", "New note"),
        Binding("o", "note_open", "Open note"),
        Binding("a", "play('audio')", "Audio"),
        Binding("v", "play('video')", "Video"),
        Binding("x", "stop_media", "Stop"),
        Binding("c", "claude", "Claude"),
        Binding("l", "local_model", "Local model"),
        Binding("s", "snapshot", "Snapshot"),
        Binding("t", "resolver_toggle", "Resolver"),
        Binding("minus", "brightness(-10)", "Bright", key_display="-/+"),
        Binding("equals_sign,plus", "brightness(10)", "Bright+", show=False),
        Binding("d", "desktop_mode", "Desktop"),
        Binding("b", "reboot", "Reboot"),
        Binding("h", "poweroff", "Power off"),
    ]
    # Which tab each action belongs to; the footer only shows (and the key only works) there.
    ACTION_TAB = {"refresh": "stat", "cycle_profile": "stat", "focus_search": "data", "note_new": "data",
                  "note_open": "data", "play": "radio", "stop_media": "radio", "claude": "ai",
                  "local_model": "ai", "snapshot": "sys", "resolver_toggle": "sys",
                  "brightness": "sys", "desktop_mode": "sys", "reboot": "sys", "poweroff": "sys"}
    BUTTON_ACTIONS = {"note-new": "note_new", "note-open": "note_open", "play-audio": "play('audio')",
                      "play-video": "play('video')", "play-stop": "stop_media", "ai-claude": "claude",
                      "ai-local": "local_model", "snap-new": "snapshot", "resolver-toggle": "resolver_toggle",
                      "bright-down": "brightness(-10)", "bright-up": "brightness(10)",
                      "sys-desktop": "desktop_mode", "sys-reboot": "reboot", "sys-poweroff": "poweroff"}

    def __init__(self, backend: Backend, runner: Runner, backend_name: str = "",
                 notes_dir: Path | None = None) -> None:
        super().__init__()
        self.backend = backend
        self.runner = runner
        self.backend_name = backend_name
        self.notes_dir = notes_dir or Path(os.environ.get("POCKET_TUI_NOTES_DIR") or Path.home() / "notes")
        self.profile = "balanced"
        self.brightness = 60
        self.resolver_enabled = True
        self.media_proc: subprocess.Popen | None = None
        self.claude_session = False
        runner.log = self.log_line
        self.register_theme(PHOSPHOR)
        self.theme = "phosphor"

    # -- composition and lifecycle --

    def compose(self) -> ComposeResult:
        yield PocketHeader(id="header")
        with TabbedContent(id="tabs"):
            yield StatPane(TABS["stat"], id="stat")
            yield DataPane(TABS["data"], id="data")
            yield RadioPane(TABS["radio"], id="radio")
            yield AiPane(TABS["ai"], id="ai")
            yield SysPane(TABS["sys"], id="sys")
        yield Footer()

    def on_mount(self) -> None:
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self._apply_width(self.size.width)
        self.sys_pane.show_brightness(self.brightness)
        self.refresh_status()
        self.refresh_sys()
        self.refresh_notes()
        self.set_interval(REFRESH_S, self.refresh_status)

    def on_resize(self, event: Resize) -> None:
        self._apply_width(event.size.width)

    def _apply_width(self, width: int) -> None:
        try:
            self.screen.set_class(width < NARROW_BELOW, "narrow")
        except ScreenStackError:
            pass  # the first resize arrives before the screen exists

    @property
    def header(self) -> PocketHeader:
        return self.query_one(PocketHeader)

    @property
    def stat_pane(self) -> StatPane:
        return self.query_one(StatPane)

    @property
    def data_pane(self) -> DataPane:
        return self.query_one(DataPane)

    @property
    def radio_pane(self) -> RadioPane:
        return self.query_one(RadioPane)

    @property
    def ai_pane(self) -> AiPane:
        return self.query_one(AiPane)

    @property
    def sys_pane(self) -> SysPane:
        return self.query_one(SysPane)

    @property
    def active_tab(self) -> str:
        try:
            return self.query_one(TabbedContent).active
        except NoMatches:
            return "stat"

    # -- tabs, keys, buttons --

    def action_switch_tab(self, name: str) -> None:
        self.query_one(TabbedContent).active = name

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        self.refresh_bindings()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """False hides the binding from the footer and makes its key inert on other tabs."""
        tab = self.ACTION_TAB.get(action)
        return tab is None or tab == self.active_tab

    def action_defocus(self) -> None:
        self.screen.set_focus(None)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id.startswith("prof-"):
            self.set_profile(button_id.removeprefix("prof-"))
        elif button_id in self.BUTTON_ACTIONS:
            await self.run_action(self.BUTTON_ACTIONS[button_id])

    # -- plumbing: threads, the terminal, logging --

    def run_in_thread(self, fn: Callable[..., Any], *args: Any, done: Callable[[Any], None] | None = None) -> None:
        """Run a backend call off the UI thread; ``done(result)`` runs back on it."""

        def job() -> None:
            try:
                result = fn(*args)
            except Exception as exc:
                self.call_from_thread(self.notify, f"{fn.__name__} failed: {exc}", severity="error")
                return
            if done is not None:
                self.call_from_thread(done, result)

        self.run_worker(job, thread=True, group="calls", exit_on_error=False)

    @contextmanager
    def _terminal(self) -> Iterator[None]:
        """Hand the terminal to another program; a no-op where suspending is impossible (tests)."""
        try:
            with self.suspend():
                yield
        except SuspendNotSupported:
            yield

    def run_in_terminal(self, argv: list[str], title: str, ai: bool = False) -> None:
        self.claude_session = ai
        self.header.ai_active = ai or self.header.ai_active
        try:
            with self._terminal():
                code = self.runner.interactive(argv)
        except RunnerError as exc:
            self.notify(str(exc), severity="error")
            return
        finally:
            self.claude_session = False
            self.header.ai_active = False
        self.notify(f"{title} exited with code {code}" if code else f"{title} finished")

    def log_line(self, line: str) -> None:
        try:
            self.query_one("#cmd-log", Log).write_line(f"{datetime.now():%H:%M:%S} {line}")
        except NoMatches:
            pass

    def export_text(self) -> str:
        """The current screen as plain text (for ``--once`` and the tests); mirrors export_screenshot."""
        width, height = self.size
        console = Console(width=width, height=height, file=io.StringIO(), force_terminal=True,
                          color_system="truecolor", record=True, legacy_windows=False, safe_box=False)
        console.print(self.screen._compositor.render_update(full=True, screen_stack=self._background_screens))
        return console.export_text()

    # -- STAT --

    @work(thread=True, exclusive=True, group="status")
    def refresh_status(self) -> None:
        b = self.backend
        data = (b.device_status(), b.power_status(), b.net_status(), b.audit_tail(20),
                self.runner.is_running("claude"))
        self.call_from_thread(self._show_status, *data)

    def _show_status(self, dev: dict, pwr: dict, net: dict, audit: list[str], claude_running: bool) -> None:
        self.profile = pwr.get("profile", self.profile)
        host = dev.get("hostname", "?") + (" [demo]" if self.backend_name == "demo" else "")
        self.header.show(host, pwr, net)
        self.header.ai_active = claude_running or self.claude_session
        self.stat_pane.show(dev, pwr, net)
        self.ai_pane.show_audit(audit)

    def action_refresh(self) -> None:
        self.refresh_status()
        self.refresh_sys()

    def set_profile(self, name: str) -> None:
        def applied(result: dict) -> None:
            self.notify(result.get("message") or f"profile: {result.get('profile', name)}",
                        severity="information" if result.get("ok", True) else "error")
            self.refresh_status()

        self.run_in_thread(self.backend.set_power_profile, name, done=applied)

    def action_cycle_profile(self) -> None:
        current = PROFILES.index(self.profile) if self.profile in PROFILES else 0
        self.set_profile(PROFILES[(current + 1) % len(PROFILES)])

    # -- DATA --

    def action_focus_search(self) -> None:
        self.query_one("#kb-query", Input).focus()

    @on(Input.Submitted, "#kb-query")
    def _search(self, event: Input.Submitted) -> None:
        if query := event.value.strip():
            self.run_in_thread(self.backend.kb_search, query, done=self.data_pane.show_results)

    @on(ListView.Selected, "#kb-results")
    def _open_result(self, event: ListView.Selected) -> None:
        if url := getattr(event.item, "payload", None):
            self.runner.open_url(url)
            self.notify(f"opening {url}")

    @on(ListView.Selected, "#notes-list")
    def _open_note_row(self, event: ListView.Selected) -> None:
        self.action_note_open()

    def refresh_notes(self) -> None:
        notes = sorted(self.notes_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        self.data_pane.show_notes(notes)

    def action_note_new(self) -> None:
        now = datetime.now()
        path = self.notes_dir / now.strftime("%Y-%m-%d-%H%M%S.md")
        path.write_text(f"# {now:%Y-%m-%d %H:%M}\n\n", encoding="utf-8")
        self.refresh_notes()
        self.open_editor(path)

    def action_note_open(self) -> None:
        notes = self.query_one("#notes-list", ListView)
        item = notes.highlighted_child or (notes.children[0] if notes.children else None)
        path = getattr(item, "payload", None)
        if path is None:
            self.notify("no note selected", severity="warning")
        else:
            self.open_editor(path)

    def open_editor(self, path: Path) -> None:
        self.run_in_terminal(shlex.split(os.environ.get("EDITOR") or "nano") + [str(path)], "editor")

    # -- RADIO --

    def action_play(self, mode: str) -> None:
        target = self.query_one("#media-target", Input).value.strip()
        if not target:
            self.notify("enter a URL or search terms first", severity="warning")
            return
        self.action_stop_media(quiet=True)
        source = target if "://" in target else f"ytdl://ytsearch1:{target}"
        if mode == "audio":
            argv = ["mpv", "--no-video", "--ytdl-format=bestaudio/best", source]
        else:
            argv = ["mpv", "--fs", "--ytdl-format=bestvideo[height<=720]+bestaudio/best", source]
        try:
            self.media_proc = self.runner.spawn(argv)
        except RunnerError as exc:
            self.notify(str(exc), severity="error")
            return
        verb = "demo, logged only" if self.runner.dry_run else "playing"
        self.radio_pane.set_status(f"{verb} ({mode}): {target}")

    def action_stop_media(self, quiet: bool = False) -> None:
        if self.media_proc is not None:
            self.runner.stop(self.media_proc)
            self.media_proc = None
            self.radio_pane.set_status("stopped")
        elif not quiet:
            self.radio_pane.set_status("nothing playing")

    # -- AI --

    def action_claude(self) -> None:
        exe = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude")
        if not (self.runner.dry_run or Path(exe).exists()):
            self.notify("claude not found: run provision stage 50", severity="error")
            return
        self.run_in_terminal([exe], "Claude", ai=True)

    def action_local_model(self) -> None:
        exe = Path.home() / ".local" / "bin" / "llama-chat"
        if self.runner.dry_run or exe.exists():
            self.run_in_terminal([str(exe)], "local model")
        else:
            self.notify("no local model yet: ~/.local/bin/llama-chat is missing (phase 2)", severity="warning")

    # -- SYS --

    def refresh_sys(self) -> None:
        self.run_in_thread(self.backend.snapshot_list, done=self.sys_pane.show_snapshots)
        self.run_in_thread(self.backend.resolver_status, done=self._show_resolver)

    def _show_resolver(self, status: dict) -> None:
        self.resolver_enabled = bool(status.get("enabled"))
        self.sys_pane.show_resolver(status)

    def action_snapshot(self) -> None:
        def created(result: dict) -> None:
            self.notify(result.get("message", "done"), severity="information" if result.get("ok") else "error")
            self.refresh_sys()

        def with_label(label: str | None) -> None:
            if label is not None:
                self.run_in_thread(self.backend.snapshot_create, label or "manual", done=created)

        self.push_screen(PromptScreen("Snapshot label", "e.g. before-upgrade"), with_label)

    def action_resolver_toggle(self) -> None:
        self.run_in_thread(self.backend.resolver_set, not self.resolver_enabled, done=lambda _: self.refresh_sys())

    def action_brightness(self, delta: int) -> None:
        wanted = max(5, min(100, self.brightness + delta))

        def applied(result: dict) -> None:
            self.brightness = int(result.get("pct", wanted))
            self.sys_pane.show_brightness(self.brightness)

        self.run_in_thread(self.backend.set_brightness, wanted, done=applied)

    def action_desktop_mode(self) -> None:
        self.confirm_then("Switch to desktop mode? The console session, and the Pocket TUI with it, will close.",
                          ["sudo", "-n", "pocket-mode", "desktop"])

    def action_reboot(self) -> None:
        self.confirm_then("Reboot now?", ["sudo", "-n", "systemctl", "reboot"])

    def action_poweroff(self) -> None:
        self.confirm_then("Power off now?", ["sudo", "-n", "systemctl", "poweroff"])

    def confirm_then(self, question: str, argv: list[str]) -> None:
        def answered(yes: bool | None) -> None:
            if not yes:
                return
            try:
                code, output = self.runner.quiet(argv)
            except RunnerError as exc:
                self.notify(str(exc), severity="error")
                return
            self.notify(f"{' '.join(argv[2:])}: {'ok' if code == 0 else output or f'exit {code}'}",
                        severity="information" if code == 0 else "error")

        self.push_screen(ConfirmScreen(question), answered)


def make_app(demo: bool = False) -> PocketTui:
    backend, name = load_backend(demo)
    return PocketTui(backend=backend, runner=Runner(dry_run=demo), backend_name=name)


async def render_once(app: PocketTui, size: tuple[int, int] = (80, 24)) -> str:
    """Mount the app headlessly, let the first refresh land, and return the screen as text."""
    async with app.run_test(size=size) as pilot:
        for _ in range(3):
            await pilot.pause()
            await app.workers.wait_for_complete()
        return app.export_text()
