# 0011 — Three views on one backend: Tiles (Windows 8 style), Desktop, Console

Status: proposed (2026-10-17). Extends 0008.

**Context.** The builder wants a Windows 8 style app view and a traditional desktop. The console view
(Pocket TUI) already exists for SSH and low power. All three should show the same live state.

**Decision.**
- **Desktop:** the stock Raspberry Pi OS labwc session with its panel.
- **Tiles:** Win8DE (GPL-2.0, Qt 6 and QML, wlr-layer-shell), a Windows 8 Start screen, lock screen and
  on-screen display built for labwc. Live tiles for the device follow its tile contract: a `logic.py` and/or
  `tile.qml` in `~/.config/Win8Start/tiles/<name>/`, each calling pocket_core for battery and hours left,
  ad blocking, GPS fix, offline library search, messages, and a Claude tile.
- **Console:** Pocket TUI, unchanged.
- A hardware button or the Super key toggles Tiles over the Desktop, as Windows 8 did.

**Alternatives.** nwg-drawer (a full-screen app grid, no live tiles). KDE Plasma's Application Dashboard
(heavier on 4 GB). Our own start screen in Python with GTK 4 and gtk-layer-shell, keeping the same tile
contract: the fallback if Win8DE does not build on Raspberry Pi OS or handles touch badly.

**Consequences.** Qt 6 adds memory use, to be measured on the 4 GB board. Win8DE's touch support and
aarch64 build are undocumented and must be tested. Tiles reuse pocket_core, so the CLI, the MCP server,
Pocket TUI and the tiles never disagree about the device's state.

Sources: [Win8DE](https://github.com/er-bharat/Win8DE),
[nwg-drawer](https://github.com/jasonherald/nwg-drawer),
[gtk-layer-shell](https://packages-cdn-origin.gentoo.org/packages/gui-libs/gtk-layer-shell).
