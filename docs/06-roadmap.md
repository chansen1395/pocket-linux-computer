# 06 — Roadmap

## MVP definition (phase 1 done means all of these are true)

1. The Pi 5 boots from a 2 TB NVMe with root on btrfs, from a rescue-able image built by `provision/run.sh`.
2. The 7" display and a keyboard work; console mode and desktop mode both exist and switch cleanly.
3. Firefox, VSCodium with the Claude Code extension, and Claude Code CLI all run on the device.
4. Ads are blocked on Wi-Fi, phone tether, and the hotspot (all five acceptance tests in `04` pass).
5. A power bank runs it for a full working day; measured, not estimated.
6. The v1 slab enclosure prints, closes, and does not throttle under a 30-minute build job.
7. A restic backup to a repository you configure restores successfully once.
8. Data volume encrypted; device survives a reboot with the passphrase typed on its own keyboard.

## Phases

| Phase | Goal | Depends on |
|---|---|---|
| **0 — Foundation** (done) | Plan, decisions, provisioning skeleton, CAD skeleton | — |
| **1 — Bench MVP** | Hardware on a desk, running the full software stack, powered from a bank; v0 tray enclosure | Parts ordered (BOM §7 in `01`) |
| **2 — Slab** | v1/v2 enclosure, integrated UPS, encoder and buttons, Pocket TUI v1, pocket MCP v1, offline knowledge pack, GPS, LoRa | Phase 1 measurements |
| **3 — Wearable** | Cradle, clip, keyboard base; LTE; SDR; audio; local AI profile; nightly self-maintenance | Phase 2 |
| **4 — Hardening** | Weather sealing, custom keyboard, e-ink status display, solar validation, NixOS evaluation | Phase 3 |

## Phase 1 task list (in order)

- [ ] Order the phase-1 BOM. Confirm the NVMe drive is on the tested list before buying.
- [x] Pi 5 4 GB and a 64 GB microSD on the desk (2026-10-16). No card reader: flash through the Pi's
      USB mass-storage mode (`provision/runbooks/00-flash-from-pc.md`; kit in `flash-kit/`).
- [x] First boot: cloud-init sets hostname/user/Wi-Fi/SSH, unpacks this repo to `~/pocket` and runs stage 10
      (log: `/var/log/pocket-firstboot.log`). Done 2026-10-16; Claude sign-in still pending.
- [x] Stages 10 and 30–80 run on the SD card (2026-10-16): resolver 5/5, Claude Code + MCP, Pocket TUI, Kiwix (42
      archives), desktop apps, llama.cpp + models, 21 GB trove. NVMe stage (20) waits for the hardware.
- [ ] Fit the NVMe base; run stage 20 (storage): EEPROM boot order, Gen 3 test, image copy, btrfs convert.
- [ ] Boot from NVMe; run stages 30–60.
- [ ] Measure: idle, console, desktop, build-job wattage with a USB-C inline meter; thermals with and without the cooler.
- [ ] Fit the display; set rotation; test touch in both modes.
- [~] Run the five ad-block acceptance tests on home Wi-Fi (passed 2026-10-16), on the phone tether, and with the hotspot up.
- [ ] Print the fit-test coupons, then the v0 tray.
- [ ] Record measurements and move decisions 0001–0006 from *proposed* to *accepted* or supersede them.

## Risks, ranked

| Risk | Impact | Mitigation |
|---|---|---|
| 4 GB RAM too small for desktop + VSCodium + Firefox | Daily use is miserable | zram, strict profiles, measure early; 8 GB board as the fallback |
| NVMe at Gen 3 drops out | Data loss | Default to Gen 2 until a week of stability; btrfs scrub + backups |
| Heat in a sealed slab | Throttling, battery aging | Cooler vents + aluminum plate; endurance profile caps CPU |
| UPS board pogo-pin contact | Spontaneous shutdowns | Enclosure clamps the stack; power bank remains a fallback |
| btrfs conversion goes wrong | Unbootable NVMe | Rescue SD; stage has a dry run and a verified rollback |
| LUKS passphrase on a tiny keyboard | The builder stops using encryption | fscrypt alternative; a USB key file as a second factor |
| Scope creep (games, SDR, LTE) | MVP never ships | Phases are gates; nothing from phase 3 shapes phase 1 hardware |

## Measuring success

- Hours of real use per charge (target 8, floor 5).
- Seconds from power button to usable console (target 20).
- Minutes to rebuild from a blank image with `provision/run.sh` (target 30, unattended).
- Days between manual fixes that were not folded back into the repo (target: never).
