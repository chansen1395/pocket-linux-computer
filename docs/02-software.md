# 02 — Software

## 1. Operating system: Raspberry Pi OS 64-bit (Bookworm or Trixie), rebuilt from scripts

Why: the only OS with first-party support for every Pi 5 peripheral we care about (DSI display,
PCIe, RTC, power button, the Pi-optimized Firefox build, `rpi-eeprom`). Debian underneath, so
Claude Code's official Debian support applies.

Considered and parked:

- **NixOS.** A declarative system is the ideal thing for an AI to manage, and rollbacks are free.
  Pi 5 support still needs a custom kernel from `nixos-hardware`, and the display and PCIe paths lag.
  Revisit once the hardware is stable; the provisioning stages are written so they could be ported.
- **Ubuntu / postmarketOS / Mobian.** Touch-first shells (Phosh, Plasma Mobile) are tempting for the
  slab form factor, but Pi 5 support is uneven and we would be fighting the display stack.
- **Alpine.** Tiny and fast, but the desktop and VS Code story is weaker. A candidate for the rescue SD.

The repo is the source of truth. `provision/run.sh` applies numbered, idempotent stages to a fresh
image; anything done by hand is folded back into a stage or lost on the next rebuild.

## 2. Two modes

| | Console mode | Desktop mode |
|---|---|---|
| What | A fullscreen terminal UI (Pocket TUI) under the `cage` kiosk compositor | labwc Wayland desktop from Raspberry Pi OS |
| For | Status, notes, messages, maps, Claude chat, music, launching things, one-handed use | Firefox, VS Code, media, anything with a window |
| Power | Low: CPU capped, backlight dimmed, Wi-Fi scanning off | Full |
| Switch | A physical button or a systemd target switch, ~2 s | Same |

Pocket TUI (`tui/`, v0 built 2026-10-16) is a Python **Textual** app: keyboard- and touch-driven,
phosphor-green, renders in a terminal so it also works over SSH from a phone, and is trivial for
Claude Code to extend. v0 has five tabs: STAT (device, power, network), DATA (offline library search,
notes), RADIO (watch/listen via yt-dlp + mpv; SDR and Meshtastic placeholders), AI (Claude Code,
local model, audit log) and SYS (snapshots, resolver toggle, brightness, mode switch, reboot). It
reads the device through `pocket_core` (`core/`) and falls back to a fake backend for development.

## 3. Applications

| Job | Choice | Notes |
|---|---|---|
| Browser | Firefox from the Raspberry Pi OS repo + enterprise policies + uBlock Origin (arkenfox `user.js` planned) | LibreWolf (Flatpak) if its arm64 build is current; Chromium only for a site that breaks, never Chrome |
| Editor | VSCodium (telemetry off by default) with the Claude Code extension from Open VSX | VS Code from the Pi repo as fallback; `code-server` so a phone browser can edit on the Pi |
| Terminal | `foot` (Wayland) + `tmux`; `mosh` for flaky mobile links | |
| AI | Claude Code CLI (native installer, arm64) | See `03-ai-integration.md` |
| Files and sync | Syncthing to a home server and the laptop; `restic` backups to a repository you configure | Nothing here is preconfigured; see `provision/config/etc/pocket/restic.env.example` |
| Mail / chat | Thunderbird; Element or Fractal for Matrix; Meshtastic client for the mesh | |
| Media | `mpv` for everything; `yt-dlp` feeding `mpv` for YouTube (no ads, no player); Jellyfin client against a home server when home | yt-dlp comes from pipx, not apt: Debian's copy ages fast and YouTube breaks it |
| Offline knowledge | Kiwix (`kiwix-serve` + `kiwix-tools`) with ZIM files: Wikipedia, WikiMed, iFixit, Gutenberg, StackExchange | This is what the 2 TB is for; ~150 GB for a serious set |
| Offline maps | Organic Maps (Flatpak, arm64) with downloaded regions; `gpsd` for the GPS module | |
| Reading | Foliate (ebooks), Zathura or Okular (PDF) | |
| Radio | `gqrx` or `SDR++` with an RTL-SDR; NOAA weather, aviation, FM | Phase 3 |
| Games | RetroArch with `mgba` (Game Boy), `mupen64plus`, PPSSPP | After MVP; the hardware is never chosen for this |

## 4. Resilience

- **Rescue microSD** in the slot at all times (plain OS + this repo). EEPROM boot order tries NVMe first.
- **Snapshots.** Root on **btrfs** with subvolumes, so a snapshot takes a second and a rollback is a
  reboot. Raspberry Pi OS ships ext4; the conversion is a documented one-time step (`btrfs-convert`
  from the rescue SD) and is the riskiest part of provisioning, so it is its own stage with a dry run.
  Fallback if btrfs misbehaves on the Pi: `timeshift` in rsync mode on ext4.
- **Watchdog.** `dtparam=watchdog=on` plus `RuntimeWatchdogSec=15` so a hang reboots.
- **zram** swap (zstd, 50 % of RAM) to stretch the 4 GB.
- **Unattended security updates** only; kernel/firmware upgrades are a deliberate stage, never automatic.
- **Backups.** `restic` to a repository you configure, nightly when reachable (the timer does nothing until it is configured); Syncthing for the live folders.

## 5. Security and privacy baseline

- Full details in `04-privacy-adblock.md`. Summary: local filtering DNS resolver, firewall that
  forces every DNS query through it, hardened Firefox, no Chrome, no telemetry.
- **Encryption at rest.** LUKS on the data volume (everything except `/boot/firmware` and the base
  system) with a passphrase at boot, typed on the device keyboard. `fscrypt` on `/home` is the
  lighter alternative if boot-time entry is too annoying on the strap. Decided in `docs/decisions/0006`.
- **Firewall:** nftables, default-deny inbound; SSH and mosh are the only open ports; hotspot mode gets its own chain.
- **SSH:** keys only. A phone reaches the device with `mosh` and attaches to the tmux session.
- **Secrets:** `pass` (GPG) for tokens; Claude Code uses the subscription login, not a long-lived API key
  on disk, so a stolen device is fixed by revoking the session.
- **Wi-Fi MAC randomization** on, Bluetooth off by default in console mode.

## 6. Memory plan for the 4 GB board

| Profile | Running | Approx. RAM |
|---|---|---|
| Console | cage + foot + Pocket TUI + resolver + daemons | 0.6 GB |
| Desktop | labwc + Firefox (5 tabs) + VSCodium + Claude Code | 3.0 GB |
| Local AI | console + llama.cpp with a 1.5B Q4 model + whisper.cpp tiny | 2.2 GB |

Desktop and Local AI do not run together. zram covers the spikes. If this proves too tight in
practice, the 8 GB board is the fix, and nothing else changes.
