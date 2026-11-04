# provision/ — turn a fresh Raspberry Pi OS image into the Pocket device

**Status: the stages ran on a real Pi 5 (stages 10 and 30 to 80, on the microSD, 2026-10-16). Stage 20 (the
NVMe stage) has not run on the device, and the display, battery and case are not built.** Treat every stage as a draft: run it first with `DRY_RUN=1`, then
for real on the rescue SD, then on the NVMe. Fold every fix back here.

```
run.sh            the runner: sudo ./run.sh --list | 10 30 | all      (DRY_RUN=1 to preview)
lib.sh            shared helpers; every helper is idempotent
stages/NN-*.sh    numbered stages, each safe to re-run
config/           files copied onto the Pi (config/etc/** mirrors /etc/**, config/home/** mirrors ~)
runbooks/         manual procedures that are too risky to automate yet (NVMe copy, btrfs conversion)
test/             arm64 container test and its results
```

| Stage | Does | Reboot? |
|---|---|---|
| 10-base | hostname, packages, zram, watchdog, RTC charging, power-off-on-halt, key-only SSH (enabled only when an authorized key exists), `/data` | yes (EEPROM) |
| 20-storage | PCIe on (Gen 2 by default), NVMe-first boot order; points at the runbook for the copy and btrfs | yes |
| 30-network | NetworkManager `dns=none`, Blocky on 127.0.0.1, nftables DNS redirect, DoT block and DoH block for listed IPv4 resolvers, MAC randomization; `--test` runs the acceptance checks | no |
| 40-desktop | Firefox + policies + uBlock Origin, VSCodium, foot, cage, mpv, yt-dlp, console/desktop targets | no |
| 50-ai | Claude Code (native installer, as the user), tmux, `pocket-helper`, hooks that snapshot before risky commands (they need a btrfs root), audit log | no |
| 55-pocket-apps | venv with `pocket_core` (CLI + MCP server) and `pocket_tui` from this repo, `pocket-helper` and its sudo rule, MCP registered with Claude Code, console mode runs the Pocket TUI | no |
| 60-backup | restic + Syncthing installs and unit templates (restic needs a repository you provide) | no |
| 70-knowledge | kiwix-tools, kiwix-serve on 127.0.0.1:8090, the small ZIM manifest | no |
| 75-trove | the offline pack from `config/knowledge/trove-manifest.txt`, about 21 GB (filter and budget via env) | no |
| 80-local-ai | llama.cpp from source, Qwen2.5-1.5B Q4 chat model, `llama-chat` wrapper | no |

Testing without a Pi: `provision/test/container-test.sh` builds an arm64 Debian 13 image that mimics
Raspberry Pi OS (Pi apt repo, a `tester` user, fake `config.txt`, no running systemd) and runs the stages in
it. It needs Docker with arm64 emulation (QEMU), takes a long time, and was last run on 2026-10-16, before the
cleanup for this repository. Stages work without a live systemd through the `svc` helper in `lib.sh` (enable
works, start is skipped), which is also what makes pre-baking an image in a chroot possible later.

Static check: `shellcheck -x -S warning run.sh lib.sh stages/*.sh test/container-test.sh config/usr/local/bin/pocket-{audit,backup,mode,snapshot} config/home/.local/bin/llama-chat`
(`config/usr/local/bin/pocket-helper` is Python; its checks are in `core/tests/test_helper.py`).

## Conventions

- Run as root via `sudo`; stages act on the invoking user (`$SUDO_USER`) for home-directory things. Set
  `POCKET_USER` to act for another account. No default user name is assumed.
- A stage never asks questions. Inputs come from environment variables with safe defaults
  (`POCKET_HOSTNAME`, `POCKET_PCIE_GEN`, `POCKET_USER`).
- Nothing site-specific lives in the repository. Wi-Fi names, passwords, SSH keys, backup repositories and
  account names come from files you create from the `*.example` templates (`flash-kit/`,
  `config/etc/pocket/restic.env.example`) and are never committed.
- Files under `/etc` are backed up once to `<name>.pocket.bak` before the first edit.
- A stage that changes boot settings touches `/var/lib/pocket/needs-reboot`; the runner tells you at the end.
- Nothing here writes to the microSD when running from NVMe or vice versa; the runbooks do that, on purpose.

## Downloads

The stages download everything at run time; no model, map or library file is in this repository. Sources and
licenses are listed in `../docs/research/trove.md`, with exact URLs and checksums in
`config/knowledge/trove-manifest.txt`.

The code the stages download and run (installers, binaries, a source build, apt keys) is listed in the root
[README](../README.md#code-that-provisioning-downloads) with what is pinned and what is not.
