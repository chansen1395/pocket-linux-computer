# Container test results

## 2026-10-16 — arm64 Debian 13.7 (QEMU on the Windows PC), image `pocket-test`

Command: `provision/test/container-test.sh` (dry run of all stages, then the real run; resumed from a
locally saved image after fixing the issues below).

| Stage | Result | Notes |
|---|---|---|
| dry run, all stages | pass | prints a sensible plan for every stage, no errors |
| 10-base | pass | all packages install (incl. `rpi-eeprom` from the Pi repo), zram config, config.txt edits, sshd drop-in |
| 20-storage | pass | config.txt PCIe lines; EEPROM skipped cleanly (no tool) |
| 30-network | pass | Blocky v0.26.2 arm64 downloaded and installed, configs owned by `blocky`, service enabled offline; nft check skipped for lack of netlink |
| 55-pocket-apps | pass | venv on Python 3.13, `pocket_core` + `pocket_tui` installed as aarch64 wheels, sudoers written, console service patched |
| 50-ai | pass | Claude Code 2.1.301 installed via the native installer for the test user; hooks and settings in place |
| 60-backup | pass | restic + syncthing installed, units and timer enabled offline |
| 70-knowledge | pass | kiwix-tools installed, test ZIM downloaded, `library.xml` built, service enabled |
| 40-desktop | not run | heavy (Firefox, VSCodium); run on the device |
| final checks | pass | `blocky version`, `claude --version`, `pocketctl status`, `pocket-tui --once` all OK |

Validated separately: `nft -c -f nftables.conf` passes on an amd64 Debian 13 container with a real
kernel (after creating the `blocky` user).

## Fixed because of this run

1. `apt-get update` fails on the Raspberry Pi archive key under Debian 13's `sqv` policy; only the test
   image is affected (the Pi image ships its own keyring) so the Dockerfile uses `trusted=yes`.
2. `nft -c` needs netlink; stage 30 now distinguishes "no netlink here" (warn) from a parse error (die).
3. `openssh-server` added to the stage 10 package list (preinstalled on Pi OS, absent on plain Debian).
4. Stage 30 no longer calls `dig` unless it is installed and a resolver can be running.
5. Kiwix manifest names corrected to the real current filenames.

## Not provable in a container (check on the device)

EEPROM settings, PCIe/NVMe, service start-up order, the firewall actually loading, NetworkManager
DNS hand-off, hotspot mode, `vcgencmd` readings, backlight, Claude sign-in.

This run predates the cleanup for the public release (renames, removal of the remote-access stage, the
`tester` user). The container test has not been re-run since; see the repository README.
