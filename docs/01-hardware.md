# 01 — Hardware

Status: options surveyed 2026-10-16 from vendor pages and the official Pi docs. Measurements from the
real board were added 2026-10-16 (section 5). **The current parts list is [08-shopping-list.md](08-shopping-list.md)**
(compact layout, decision 0010); this document keeps the wider survey. Items marked **verify** need
confirmation on real parts.

## 1. Compute: Raspberry Pi 5, 4 GB

Fixed by the builder. Consequences:

- **RAM is the tight resource.** VS Code (~0.5–1 GB), Firefox (~0.5 GB per few tabs), Claude Code
  (~0.3 GB) and a desktop fit in 4 GB with zram swap, but not alongside a local language model.
  Design rule: Desktop mode and local-model mode are separate power profiles, not simultaneous.
- **Power input.** The Pi 5 wants 5 V / 5 A for full USB peripheral current. On a 5 V / 3 A
  source it boots fine but limits USB to 600 mA unless `usb_max_current_enable=1` is set.
  A Bluetooth keyboard and a DSI display keep the USB budget tiny, so 3 A sources work.
- **Built in:** Wi-Fi 5, Bluetooth 5, real-time clock (add the official RTC battery), a power
  button, a 4-pin fan header, one PCIe 2.0 x1 FPC connector (Gen 3 works unofficially), two
  22-pin MIPI connectors (camera or display), Gigabit Ethernet, 2× USB 3, 2× USB 2, 2× micro-HDMI.
- **No 3.5 mm audio jack.** Audio goes over HDMI, USB, Bluetooth, or an I2S DAC/amp on GPIO.
- **Cooling:** the official Active Cooler (fan + heatsink, PWM via the fan header) or a large
  passive plate that doubles as chassis structure. The Pi 5 throttles at 85 °C; a sealed slab
  needs one or the other.

## 2. Storage: 2 TB NVMe, boot from NVMe

Recommendation: **bottom-mount M.2 board that takes 2280 drives**, because 2 TB in the small
2230 size costs roughly double and the official M.2 HAT+ only takes 2230/2242.

| Board | Mount | Sizes | Notes |
|---|---|---|---|
| Pimoroni NVMe Base | under the Pi, same footprint | 2230–2280 | Sells a bundle with a tested 2 TB drive; keeps the de-facto compatibility list other vendors point to |
| 52Pi N07 / PCBWay NVPI5-2280B | under the Pi | 2230–2280 | Cheaper clones of the same idea |
| Geekworm X1208 | under the Pi | M.2 + 1× 21700 | UPS and NVMe on one board; one cell is too little for us but it proves the combo works |
| Official M.2 HAT+ | on top | 2230/2242 | Cleanest cable routing; 2 TB 2230 drives exist (WD SN740, Sabrent Rocket 2230) at a premium |

Settings (go in `provision/`): `dtparam=pciex1_gen=3` in `config.txt` (official docs say Gen 3
is uncertified and "may be unstable"; test it, fall back to Gen 2 if the drive drops out),
EEPROM `BOOT_ORDER=0xf416` (NVMe, then SD, then USB), `PCIE_PROBE=1` for non-HAT+ boards.

Drive choice: pick from Pimoroni's tested list. Low idle power matters more than peak speed
because the link is x1 anyway. **verify** power draw of the chosen drive (target under 2.5 W active).

The microSD slot stays populated with a **rescue image**: plain Raspberry Pi OS plus a clone of
this repo, so a broken NVMe install can be repaired from the device itself.

## 3. Display

Recommendation: **Raspberry Pi Touch Display 2** (7", 720×1280 IPS, 5-point capacitive touch, DSI).

- Powered from the Pi's GPIO header; one ribbon to the DSI port. The 22-to-15-way cable for the
  Pi 5 is in the box. No HDMI cable, no USB for touch, no driver hunting.
- Native portrait; rotate to landscape in software (compositor config, one line).
- Active area ~88 × 155 mm, so the device is about 190 × 120 mm.
- **verify** backlight power draw (not published; expect 1.5–3 W; measure at the brightness we use).

Alternatives kept on the table:

| Display | Why / why not |
|---|---|
| Waveshare 5" DSI 800×480 | Lighter forearm variant; resolution too low for VS Code |
| Waveshare 5.5" AMOLED 1920×1080 (HDMI + USB touch) | Gorgeous, but an HDMI cable, more power, more cutouts |
| Waveshare 7" DSI 1024×600 | Landscape native, cheaper, lower pixel density |
| Small e-ink secondary (2.9"–4.2") | Always-on status (battery, GPS, messages) at near-zero power; stretch |

Sunlight readability is poor on all of these. Mitigation: high-contrast console mode, a hood
on the forearm cradle, and the e-ink stretch goal.

## 4. Input

- **Phase 1:** a compact off-the-shelf keyboard. A low-profile 60% Bluetooth board for the
  bag; a thumb-style mini keyboard (Rii-class) for the strap.
- **Phase 2 (custom):** an ortholinear low-profile board on an RP2040 running KMK (CircuitPython),
  Kailh Choc switches, 3D-printed plate and case, wired to a USB 2 port or an internal header.
  Snaps onto the bottom edge of the slab through the same mount standard as the cradles.
- **Pointing:** touchscreen first. Add a thumb trackball (Pimoroni Trackball Breakout, I2C) or a
  tiny analog stick for console mode.
- **Hand controls:** one rotary encoder with push (scroll, select, volume) and 3–4 tactile
  buttons on GPIO for mode switches, all usable with gloves. Cheap, on-theme, genuinely useful.

## 5. Power

Budget (estimates; replace with measurements):

| Load | Typical | Peak |
|---|---|---|
| Pi 5 (desktop, Wi-Fi on) | 3.0 W | 8 W |
| NVMe 2 TB | 0.5 W | 2.5 W |
| 7" display, 60 % brightness | 2.0 W | 3 W |
| Keyboard (BT) + encoder + sensors | 0.1 W | 0.5 W |
| LTE modem (when fitted) | 0.5 W | 3 W |
| Conversion losses (~12 %) | 0.7 W | 2 W |
| **Total** | **~7 W** | **~19 W** |

**Measured 2026-10-16** on the bare Pi 5 (no display, no NVMe, Ethernet + Wi-Fi up, official supply), from
`vcgencmd pmic_read_adc` rail currents × voltages: **~4.2 W while apt was installing packages** at
2400 MHz (VDD_CORE 2.58 A at 0.875 V = 2.26 W of it), 51 °C with no cooler, EXT5V 5.04 V, throttled 0x0.
First boot to login: 41 s (39 s of it userspace, desktop image); **21 s after provisioning** (1.9 s kernel +
19.2 s userspace, desktop still enabled). **Idle (headless, Ethernet + Wi-Fi up, resolver, Kiwix and
Syncthing running): 1.8–2.3 W** by the same rail sum, 46–52 °C with no cooler, 1.5–1.7 GHz. RAM at rest:
3485 MB available of 4049. microSD (64 GB card, Trixie, SD slot): 25.7 MB/s write, 93.9 MB/s read (512 MB,
fsync). **Sustained 4-core load with no cooler
(llama.cpp build, 25 °C room): 84.5 °C after ~5 minutes and `get_throttled=0xe0008`, i.e. the firmware's
soft temperature limit engaged and clocks were capped.** The Active Cooler (or a heat-spreading
chassis plate) is not optional for the slab.

**Power supply finding (2026-10-16):** on a phone-style USB-C charger (firmware negotiated 900 mA, no PD),
apt installs and a 4-core compile ran fine, but `llama-bench` with 4 threads (all cores plus full memory
bandwidth) cut the power twice within seconds: red LED only, board off, no kernel panic in the log. The
PMIC protects the board when the input sags. Consequences: the official 27 W PD supply (or any 5 V / 5 A
source) is the bench requirement; the battery board must sustain 5 A peaks (the 6 A boards in §5 do);
and the "endurance" power profile should also cap threads for local-model runs, not just clocks.
Read the negotiated limit with `od -An -tu4 --endian=big /proc/device-tree/chosen/power/max_current`.

Runtime at 7 W: a 74 Wh pack (20 000 mAh bank, or 4× 21700) gives ~9 h; 2× 21700 (~36 Wh) gives ~4.5 h.
The airline limit is 100 Wh, so 4× 21700 is the sweet spot.

**Phase 1: USB-C PD power bank.** Zero design risk, hot-swappable, charges from a folding solar
panel, and lets us measure real consumption before committing to a pack. Pick one that advertises
5 V / 3 A on USB-C and pass-through charging.

**Phase 2: integrated UPS board.** Candidates, all with pogo-pin or header connection, an I2C fuel
gauge, and charge-while-running:

| Board | Cells | Output | Charging | Notes |
|---|---|---|---|---|
| Waveshare 21700 UPS HAT (E) | 4× 21700 | 5 V / 6 A | USB-C PD up to 40 W, bidirectional | Battery level shows in Raspberry Pi OS; ~£32; also fits Pi 3/4 |
| Geekworm X1206 V2 | 4× 21700 | 5.1 V / 6 A | 9–18 V input | 4-layer PCB; ~$50 |
| Geekworm X1205 | 2× 21700 | 5.1 V / 6 A | — | Half the runtime, half the weight |
| Geekworm X1201 | 2× 18650 | 5.1 V / 5 A | — | Cheapest; 18650 cells are easy to find anywhere |

Geekworm notes its boards shut down within 3 s if they do not detect the Pi over the pogo pins, so
the enclosure must hold the stack firmly. **verify** whether the Waveshare board's PD input accepts
a solar panel's fluctuating output or needs a bank in between.

**Phase 3 (only if nothing fits): custom pack.** 2S2P 21700 with a BMS, a USB-C PD 2S charger module
(IP2368-class, common in cyberdeck builds), a 5 V / 5.5 A buck (Pololu D36V50F5), and a MAX17048 fuel
gauge on I2C. Only if the UPS boards fail on runtime, thickness or solar.

Low-power behavior: the Pi 5 has no suspend-to-RAM. "Sleep" is screen-off idle (~2.5 W) or a real
halt with `POWER_OFF_ON_HALT=1` in the EEPROM (milliwatts; wake from the power button or the RTC alarm;
NVMe boot takes ~15 s). Console mode caps the CPU and dims the backlight.

## 6. Connectivity and sensors

| Need | Part | Interface | Phase |
|---|---|---|---|
| Internet on the move | Phone tether (USB or Wi-Fi) | built in | 1 |
| Internet without a phone | USB LTE modem (Quectel EG25-G in a USB sled, or a SIM7600 HAT) | USB | 3 |
| Off-grid messaging | Meshtastic: Waveshare SX1262 SPI HAT (listed as tested) or RAK WisMesh RAK6421 HAT | SPI | 2 |
| Position | u-blox NEO-M8N/M9N module | UART (`dtparam=uart0=on`) | 2 |
| Radio listening | RTL-SDR Blog V4 dongle | USB | 3 |
| Environment | BME280 (temp/humidity/pressure) | I2C | 2 |
| Motion / orientation | BNO085 or ICM-20948 IMU | I2C | 3 |
| Camera | Camera Module 3 | CSI (the second MIPI port) | 3 |
| Audio | I2S DAC + amp (MAX98357A) + small speaker, I2S mic; or a USB-C audio adapter | I2S / USB | 2 |
| Timekeeping offline | official RTC battery (ML2020) with trickle charge enabled | built in | 1 |

Stacking rule: the UPS wants the bottom, the NVMe base wants the bottom, the display wants the DSI
port, HATs want the GPIO header. With a 7" display the device is wider than the Pi, so the plan is
**side by side, not stacked**: Pi + NVMe base in one bay, battery board in the next, sensors on a
small breakout strip wired to the header with a ribbon. See `05-enclosure.md`.

## 7. Candidate bill of materials, phase 1

| Item | Approx. cost (USD) |
|---|---|
| Raspberry Pi 5, 4 GB | 60 |
| Official 27 W USB-C power supply (bench and charging; a phone charger trips the PMIC under load) | 12 |
| Active Cooler | 5 |
| RTC battery | 5 |
| Pimoroni NVMe Base + tested 2 TB NVMe | 150–180 |
| Raspberry Pi Touch Display 2 | 60 |
| 32 GB microSD (rescue) | 8 |
| 20 000 mAh USB-C PD power bank | 40 |
| Compact Bluetooth keyboard | 25–40 |
| Rotary encoder, buttons, wiring, heat-set inserts, screws | 15 |
| PETG + TPU filament | 25 |
| **Total** | **~400–440** |

Phase 2 adds the UPS board plus 4× 21700 cells (~$75), GPS (~$20), LoRa HAT (~$30), BME280 (~$6),
I2S audio (~$15).

## Sources checked 2026-10-16

- Touch Display 2 resellers (Waveshare, Elektor, Little Bird): 7", 720×1280, DSI, GPIO-powered, Pi 5 cable included.
- Pimoroni NVMe Base product page and Gen 3 guide; 52Pi N07 and PCBWay NVPI5-2280B listings.
- The Pi Hut listing for the Waveshare 21700 UPS HAT (E); Geekworm X1201/X1202/X1205/X1206/X1208 pages.
- Pilet coverage on Liliputing, It's FOSS and Notebookcheck (reference device).
- Meshtastic "Linux native hardware" page (Pi 5 and the Waveshare SX126X SPI HAT listed as tested).
