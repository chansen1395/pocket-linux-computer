"""Starting other programs on behalf of the UI.

One class, one switch: with ``dry_run=True`` nothing is started; every call is recorded in
``history`` and reported through ``log``. That is what the tests and ``--demo`` use.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
import webbrowser
from typing import Callable


class RunnerError(Exception):
    """A program could not be started (usually: not installed)."""


class Runner:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run
        self.history: list[list[str]] = []
        self.log: Callable[[str], None] = lambda line: None

    def _record(self, argv: list[str], verb: str) -> None:
        self.history.append(list(argv))
        prefix = "would " if self.dry_run else ""
        self.log(f"{prefix}{verb}: {shlex.join(argv)}")

    def spawn(self, argv: list[str]) -> subprocess.Popen | None:
        """Start a detached background process (mpv). Returns None in dry-run."""
        self._record(argv, "spawn")
        if self.dry_run:
            return None
        detach = {"start_new_session": True} if os.name == "posix" else {}
        try:
            return subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, **detach)
        except OSError as exc:
            raise RunnerError(f"cannot start {argv[0]}: {exc}") from exc

    def stop(self, proc: subprocess.Popen) -> None:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        self.log(f"stopped pid {proc.pid}")

    def interactive(self, argv: list[str]) -> int:
        """Run a program that takes over the terminal (the app must be suspended); returns its exit code."""
        self._record(argv, "run")
        if self.dry_run:
            return 0
        try:
            return subprocess.call(argv)
        except OSError as exc:
            raise RunnerError(f"cannot run {argv[0]}: {exc}") from exc

    def quiet(self, argv: list[str], timeout: float = 30) -> tuple[int, str]:
        """Run a short command and capture what it printed."""
        self._record(argv, "exec")
        if self.dry_run:
            return 0, ""
        try:
            done = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        except OSError as exc:
            raise RunnerError(f"cannot run {argv[0]}: {exc}") from exc
        except subprocess.TimeoutExpired:
            return 124, "timed out"
        return done.returncode, (done.stdout + done.stderr).strip()

    def open_url(self, url: str) -> None:
        if sys.platform.startswith("linux") and shutil.which("xdg-open"):
            self.spawn(["xdg-open", url])
            return
        self._record(["webbrowser", url], "open")
        if not self.dry_run:
            webbrowser.open(url)

    def is_running(self, name: str) -> bool:
        """Is a process with exactly this name alive? False in dry-run or without pgrep."""
        if self.dry_run or not shutil.which("pgrep"):
            return False
        return subprocess.run(["pgrep", "-x", name], capture_output=True).returncode == 0
