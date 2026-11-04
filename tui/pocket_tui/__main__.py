"""Command line entry: ``pocket-tui`` or ``python -m pocket_tui``."""

from __future__ import annotations

import argparse
import asyncio
import sys


def parse_size(text: str) -> tuple[int, int]:
    width, height = text.lower().split("x")
    return int(width), int(height)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pocket-tui", description="Pocket console-mode UI")
    parser.add_argument("--demo", action="store_true",
                        help="use the built-in fake backend; external programs are logged, never started")
    parser.add_argument("--once", action="store_true",
                        help="render one frame headlessly, print it as text and exit (smoke test)")
    parser.add_argument("--size", default="80x24", metavar="WxH", help="terminal size for --once (default 80x24)")
    args = parser.parse_args(argv)

    from .app import make_app, render_once  # imported late so --help stays instant

    app = make_app(demo=args.demo)
    if args.once:
        text = asyncio.run(render_once(app, parse_size(args.size)))
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # box glyphs on a cp1252 console
        print(text)
        return 0
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
