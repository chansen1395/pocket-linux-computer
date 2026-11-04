# 0008 — Console mode = Textual TUI under cage; Desktop mode = labwc

Status: proposed (2026-10-16)

**Context.** 4 GB of RAM, a battery, and a one-handed use case alongside a real desktop need.

**Decision.** Two systemd targets. Console: cage kiosk compositor running foot with the Pocket TUI Textual app, CPU capped, backlight low. Desktop: the stock labwc session. A button switches.

**Alternatives.** One desktop with a launcher (always pays desktop RAM and power). A native GTK/Qt or web launcher (heavier, and not usable over SSH from a phone).

**Consequences.** Pocket TUI is a terminal app, which keeps it tiny and makes every feature usable remotely; graphical content (maps, video) opens in desktop mode or in a dedicated fullscreen window.
