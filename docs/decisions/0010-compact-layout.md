# 0010 — Compact layout: 5" display over a Pi 5 on a battery-and-SSD board, fold-out keyboard

Status: proposed (2026-10-17). Supersedes 0003 (7" display) and 0004 (power bank, then a 4-cell board);
amends 0002 (the SSD now sits on the battery board).

**Context.** The goal is the most compact build, a full keyboard with a pointing device that
slides or folds out, GPS, offline non-Google maps, HDMI out for hotel TVs, and an SSD, accepting less
capacity if size demands it. Measurements on the real board (2026-10-16) showed it throttles without a
cooler and needs a supply that delivers 5 A.

**Decision.**
- Display: Raspberry Pi Touch Display 2, 5-inch (720 × 1280, used landscape), $40.
- Stack inside the display's footprint: Pi 5 with the Active Cooler on a Geekworm X1208, which carries
  one 21700 cell, the UPS circuit (5.1 V / 5 A out, fuel gauge, safe shutdown) and an M.2 slot.
- Storage: 1 TB 2230 NVMe to start; the slot also takes 2280 for a cheaper 2 TB.
- Keyboard: a tri-fold Bluetooth keyboard with touchpad now; a custom 40 % slide-out keyboard with a
  Cirque trackpad later, only if the tri-fold falls short.
- GPS: a BN-220 on the UART pins at the top edge. Maps: CoMaps first (OpenStreetMap-based, offline,
  Flatpak for aarch64); if its Linux build lacks GPS support, a local map page from Protomaps tiles and
  gpsd (commands in research/trove.md).
- HDMI: a panel-mount micro-HDMI to full-size HDMI extension on the side of the shell.

**Alternatives.** 7" display (more usable, 50 % larger slab). Waveshare 4-cell UPS HAT (E) with USB-C PD
input (field charging from power banks and solar, four times the energy, much bigger). Pimoroni NVMe Base
plus a separate UPS board (both want the underside of the Pi). Compute Module 5 on a custom carrier
(smallest, but a PCB project). BB Q20 thumb keyboard as the only keyboard (not a full key set).

**Amended 2026-10-18 (cost).** The $370–500 parts list was too expensive. Phase 1 now runs
from a USB-C PD power bank and keeps the 64 GB microSD plus a small USB stick for storage; the X1208,
a used 512 GB NVMe, GPS and the panel HDMI port move to a later phase. The layout itself is unchanged,
so the later parts drop in without redesign. See 08-shopping-list.md.

**Consequences.** About 155 × 95 × 40 mm and 400 g before the keyboard (estimate). About 4 hours of light
use per cell, so spare cells replace a big battery. Charging needs a 5 V / 5 A source; power-bank and
solar charging must be tested and may force the Waveshare fallback. VS Code is cramped at 5", so heavy
work moves to an HDMI screen. The enclosure redesign (05-enclosure.md) follows the new footprint.
