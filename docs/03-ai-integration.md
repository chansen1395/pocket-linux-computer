# 03 — AI integration

The brief: Claude should have "its grippers in the Pi": able to inspect the device, change it,
fix it, and extend it, from the device itself or from a phone, whenever there is a connection.
And it must be safe to let it do that.

## 1. Claude Code on the device

- Install with the native installer (`curl -fsSL https://claude.ai/install.sh | bash`). Anthropic's
  requirements list Debian 10+ on ARM64 with 4 GB RAM, which is exactly this board. The npm route
  (`linux-arm64`) is the fallback.
- Sign in with the Claude subscription (OAuth), not an API key on disk. Stolen device = revoke session.
- Runs inside `tmux` so a session survives the screen turning off or the phone dropping the link.
- Three ways in:
  1. **On the device:** console mode has a "Claude" tab that opens the CLI in a pane.
  2. **From a phone:** `mosh` into the Pi and attach to the tmux session. Termux (Android)
     works well for this. Claude Code's Remote Control feature, if available on the account, replaces this.
  3. **From the laptop:** VS Code Remote-SSH to the Pi, or the Claude Code extension inside VSCodium on the Pi.
- The repo lives at `~/pocket` on the device, so "update the ad-block list and re-provision" is a
  one-line request.

## 2. The `pocket-mcp` MCP server (`core/`, installed by stage 55)

A small Python server (FastMCP) that gives Claude structured access to things a shell makes awkward. The table
is the design. What exists today is eleven tools, listed in `core/README.md` (`device_status`, `power_status`,
`net_status`, `snapshot_list`, `snapshot_create`, `resolver_status`, `resolver_set`, `kb_search`, `audit_tail`,
`set_power_profile`, `set_brightness`). Hotspot control, GPS, sensors, display mode, rollback and mesh messaging
are planned, not built.

| Tool | Does |
|---|---|
| `device.status` | temperature, throttling flags, CPU cap, RAM, disk, uptime |
| `power.status` / `power.profile(name)` | battery %, charge rate, est. runtime; switch console / desktop / endurance profiles |
| `net.status` / `net.hotspot(on/off)` | active link, signal, hotspot toggle |
| `gps.fix` | lat/lon/alt/speed from `gpsd` |
| `sensors.read` | BME280, IMU |
| `display.brightness(n)` / `display.mode(console|desktop)` | |
| `snapshot.create(label)` / `snapshot.list` / `snapshot.rollback(id)` | btrfs snapshots |
| `mesh.send(text)` / `mesh.inbox` | Meshtastic |
| `kb.search(query)` | offline Kiwix search |

Everything the server does is also a CLI (`pocketctl status`, `pocketctl power endurance`) so humans and
Pocket TUI use the same code path.

## 3. Safety net for an AI with sudo

- **Snapshot before change.** A Claude Code `PreToolUse` hook on `Bash` matches `sudo`, `apt`, edits
  under `/etc` or `/boot`, and creates a btrfs snapshot first. Cheap enough to do every time. **This needs a
  btrfs root**, which the NVMe runbook (`provision/runbooks/20-nvme-btrfs.md`) creates. On the stock ext4 install
  the hook does nothing, so until that runbook is done there is no snapshot safety net.
- **Rollback is a reboot.** The rescue SD plus `snapshot.rollback` (planned) cover the "it won't boot" case.
- **Hooks are in the repo** (`provision/config/home/.claude/settings.json`), so they are provisioned, not remembered.
- **Audit:** every Bash call Claude makes is logged by a `PostToolUse` hook to `~/.pocket/audit.log`.
- **No long-lived cloud credentials** on disk beyond the Claude session, which is revocable.
- **Deny list** in the Claude Code settings: no `rm -rf /`, no `dd` to `mmcblk0`, no EEPROM writes
  outside the provisioning stage.

## 4. Offline AI (phase 2)

With 4 GB, local models are a convenience, not a replacement:

- **llama.cpp** (arm64, NEON) with a 1–1.5B instruct model in Q4 (Qwen 2.5/3 1.5B, Llama 3.2 1B,
  Gemma 3 1B). Expect a few tokens per second. Good for summarizing a Kiwix article, drafting a
  message, answering "how do I" against the offline docs. Not for coding.
- **whisper.cpp** tiny/base for voice notes and voice commands; **Piper** for text-to-speech.
- Both run only in the Local AI power profile (desktop apps closed).
- A **local RAG** over the Kiwix ZIMs and your own notes is the stretch goal; the MCP `kb.search`
  tool is the first step.

## 5. Offline knowledge pack

Not AI, but it is what makes the AI useful offline and it is the best use of 2 TB:

| Set | Size (approx.) | Source |
|---|---|---|
| Wikipedia EN, no pictures | 50 GB | download.kiwix.org |
| Wikipedia EN, with pictures | 110 GB | same |
| WikiMed (medical) | 2 GB | same |
| iFixit, WikiHow | 5 GB | same |
| Project Gutenberg | 70 GB (or a curated 5 GB) | same |
| StackExchange (selected sites) | 20–80 GB | same |
| OpenStreetMap regions (Organic Maps) | 1–10 GB per region | Organic Maps in-app |
| Survival / first-aid / ham radio references | 1 GB | curated PDFs |

The verified list with licenses, exact URLs, sizes and checksums is `docs/research/trove.md`
(2026-10-16): a 21 GB v0 pack for the 64 GB card (WikiMed, Simple Wikipedia, iFixit, Wikivoyage,
selected StackExchange sites, Hesperian medical guides, an Army survival manual and first-aid manuals, FEMA and
state preparedness guides, ham radio references, Standard Ebooks and Gutenberg classics, Python and
Debian docs, a Geofabrik map extract, and the local AI models). Stage 70 installs Kiwix and a small
ZIM set; stage 75 downloads the pack from `provision/config/knowledge/trove-manifest.txt` with resume
and checksum verification; stage 80 builds llama.cpp and installs the chat model.

## 6. Scheduled self-maintenance (phase 3)

A nightly systemd timer runs a non-interactive Claude Code task when on charge and online:
check journal errors, disk health, pending security updates, failed backups; write a short report
to `~/.pocket/reports/`; open nothing and change nothing without the hook snapshot. Shown as a
"Health" tab in Pocket TUI.
