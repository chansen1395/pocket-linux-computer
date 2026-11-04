# 0006 — Encryption at rest: LUKS data volume, passphrase at boot

Status: proposed (2026-10-16)

**Context.** The device is meant to be carried everywhere and may be lost.

**Decision.** The base system stays unencrypted for fast, unattended boot; everything under /data and /home lives on a LUKS volume unlocked at boot with a passphrase typed on the device, with a USB key file as an optional second method.

**Alternatives.** Full-disk LUKS (slower boot, same keyboard problem). fscrypt on /home (lighter, unlocked at login; weaker for /data).

**Consequences.** Headless boots need the key file; backups and Syncthing start after unlock. Revisit if the passphrase is skipped in practice: that would mean the design failed.
