# Open questions and things to verify

Each line: what, why it matters, how to settle it. Move settled items to the relevant doc with a date.

## Hardware

- **Touch Display 2 power draw** at 50/75/100 % brightness. Drives the runtime estimate. Inline USB meter, three readings.
- **Chosen NVMe drive: idle and active watts, and Gen 3 stability** over a week of `btrfs scrub` and builds. Drives the Gen 2/3 default.
- **Waveshare UPS HAT (E): does its PD input tolerate a solar panel directly?** If not, the bank stays in the chain. Bench test with the panel on a cloudy day.
- **UPS + NVMe base + display side by side: does the GPIO header still reach the UPS pogo pins** once the Pi sits on standoffs over the NVMe base? Geekworm shuts down in 3 s without contact. Dry-fit before designing the slab.
- **Active Cooler clearance** above the Pi with the display ribbon routed over it. Measure; the v0 tray will tell.
- **GoPro mount dimensions** for the printed version. Print a test pair, check fit against a commercial mount, then freeze `cad/lib/gopro.scad`.
- **Keyboard for the strap.** Which thumb keyboard is tolerable for real typing? Buy one, try for a week.

## Software

- **Raspberry Pi OS: Bookworm or Trixie** at build time. Check which has the Firefox package and labwc stable; check Claude Code and VSCodium on both.
- **btrfs root on Pi OS.** Confirm the kernel has btrfs built in (it does on recent images) and that the initramfs handles a subvolume root. Alternative: `timeshift` on ext4.
- **LibreWolf arm64 Flatpak currency.** If it lags Firefox by more than a release, stay on the Pi Firefox with its policies (and arkenfox, once added).
- **Claude Code extension on VSCodium (Open VSX).** Documented as available; confirm it signs in and finds the CLI on arm64.
- **Claude Code Remote Control availability** on your plan, for driving the Pi session from the phone app.
- **Organic Maps Linux Flatpak on arm64.** If missing, fall back to a local tile server + a simple viewer.
- **Meshtastic pin mapping** for the Waveshare SX1262 HAT on the Pi 5 (the documented config was for a Pi 3B).
- **AdGuard Home vs Pi-hole v6 vs Blocky** memory footprint on this board. All three fit the same slot; pick the lightest that keeps a UI.
- **Hotspot + Wi-Fi client on the same radio.** The Pi 5 radio can do AP + STA concurrently on some channels; if not, the hotspot only works when internet comes from LTE or USB tether.

## Settled 2026-10-16

- **Flashing without a card reader:** the Pi 5 exposes its microSD over USB-C in rpiboot mode
  (hold the power button while plugging into the PC; host runs `rpiboot -d mass-storage-gadget64`).
  Host side prepared; the Pi was not seen on the front-panel USB ports, rear port is next. Runbook 00.
- **First boot on Trixie is cloud-init:** `user-data` + `network-config` on the boot partition;
  Imager 2.0 writes them from `--cloudinit-userdata/--cloudinit-networkconfig`; the `rpi:` block is
  flat booleans (`i2c`, `spi`, `serial`, `onewire`, `enable_usb_gadget`). We embed the repo as a tarball
  and run stage 10 from `runcmd`.
- **sshd drop-in ordering:** cloud-init writes `50-cloud-init.conf` with password auth on; ours is
  `00-pocket.conf` so it wins (sshd keeps the first value).
- **Kiwix names (download.kiwix.org, checked):** `wikipedia_en_medicine_maxi_2026-10.zim` is WikiMed;
  `ifixit_en_all_2025-12.zim`; `wikipedia_en_all_{maxi,nopic,mini}_2026-xx.zim`. No `wikihow/` folder;
  Simple English not found under `wikipedia_en_simple*` (research agent to confirm).
- **Debian 13 containers reject the Raspberry Pi archive key** (sqv policy); the real image ships
  `raspberrypi-archive-keyring`, so only the test image needs `trusted=yes`.
- **Claude Code extension is on Open VSX**, so VSCodium works (docs confirm; stage 40 installs it).
- **Resolver on the real Pi (08:43):** Blocky v0.26.2 loads OISD big + HaGeZi Pro (436k entries) in ~3 s;
  `pagead2.googlesyndication.com` is sinkholed, DoH to the listed public IPv4 resolvers is dropped. Curated lists leave the
  `doubleclick.net` apex unblocked on purpose, so tests must use an unambiguous ad host. Blocky's "fast"
  loading strategy answered (and cached) queries before the lists were in: switched to `blocking`.
- **Trixie image specifics:** PackageKit holds the apt lock for minutes after first boot (use
  `DPkg::Lock::Timeout`); the image already runs a 2 GB zram swap (do not add zram-tools); cloud-init
  honors the flat `rpi:` block (i2c, spi, enable_usb_gadget → `dtoverlay=dwc2,dr_mode=peripheral`,
  NetworkManager "USB Gadget (shared)" on usb0 10.12.194.1/28).

