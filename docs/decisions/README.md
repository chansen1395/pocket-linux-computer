# Decisions

One file per decision. Status is one of **proposed**, **accepted**, **superseded by NNNN**.
A decision moves to accepted only with a measurement or a test behind it. Supersede, never edit history.

| # | Decision | Status |
|---|---|---|
| 0001 | Raspberry Pi OS 64-bit, rebuilt from provisioning stages | proposed |
| 0002 | 2 TB NVMe on a bottom-mount 2280 base, boot from NVMe, rescue microSD | proposed |
| 0003 | Raspberry Pi Touch Display 2 (7", DSI) | superseded by 0010 |
| 0004 | Power: USB-C PD bank first, 4x 21700 UPS board second | superseded by 0010 |
| 0005 | Ad blocking: local Blocky resolver + nftables redirect + uBlock Origin | proposed |
| 0006 | Encryption at rest: LUKS data volume, passphrase at boot | proposed |
| 0007 | Enclosure: one slab, GoPro mount standard, OpenSCAD in git | proposed |
| 0008 | Console mode = Textual TUI under cage; Desktop mode = labwc | proposed, extended by 0011 |
| 0010 | Compact layout: 5" display, Pi 5 on an X1208 battery+SSD board, fold-out keyboard | proposed |
| 0011 | Three views on one backend: Tiles (Win8DE), Desktop (labwc), Console (Pocket TUI) | proposed |
