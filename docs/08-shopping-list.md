# 08 — Shopping list (revised 2026-10-18 for cost)

The first version (2026-10-17) came to $370–500, mostly the SSD. Cost was the constraint, so this version buys only what the device cannot work without and defers the rest.
Prices checked 2026-10-17/18 unless marked *list*. Memory and flash prices have doubled or tripled
in the past year, so recheck at checkout. Layout: [decision 0010](decisions/0010-compact-layout.md).

## Budget build: buy now

| # | Part | Why | ~Price |
|---|---|---|---|
| 1 | Raspberry Pi Active Cooler | The bare board hit 84.5 °C and throttled within 5 minutes | $5 *list* |
| 2 | Raspberry Pi Touch Display 2, 5-inch | 720 × 1280, powered from the GPIO header, one ribbon | $40 *list* |
| 3 | Tri-fold Bluetooth keyboard with built-in touchpad | Full key set that folds to slab size; generic clones are fine, buy where returns are easy | $30–45 |
| 4 | Micro-HDMI to HDMI cable, 1–2 m | Plug straight into a hotel TV | $7 |
| | **Essentials total** | | **about $80–95** |
| 5 | Slim 10,000 mAh USB-C PD power bank | About 37 Wh, roughly twice one 21700 cell, for less money. **Skip if you own one** | $20 |
| 6 | Raspberry Pi 27 W power supply | Desk power without brown-outs. **Skip if you own any USB-C PD charger of 15 W or more**: the phone charger that failed was not PD and gave 900 mA | $12 *list* |
| 7 | Samsung FIT Plus USB stick, 128 GB | For films and extra library space; sits almost flush in the port | $15 |
| | **Everything** | | **about $130** |

Already on hand: the Pi 5 4 GB and the 64 GB microSD, which holds the OS, the 21 GB offline library
and the models with 23 GB still free.

## Storage, cheapest first

1. **$0: keep the 64 GB card.** It already holds everything installed so far, with 23 GB free.
2. **$15–25: add a Samsung FIT Plus USB stick** (128 GB about $15, 256 GB about $23 on recent deals).
   Fast enough for films and Kiwix archives, and tiny.
3. **Later, $25–36: a used 512 GB 2230 NVMe pulled from a laptop or Steam Deck**, once there is a board
   to hold it (the X1208 below). Buy from sellers that show the drive's health percentage.

New 1 TB drives at $150–250 are not worth it while flash prices are this high.

## Later: the integrated compact build

Buy these when the case is printed and the budget build has proven itself.

| Part | What it adds | ~Price |
|---|---|---|
| Geekworm X1208 + 2 brand-name 21700 cells | Battery inside the case, safe shutdown, fuel gauge, and the SSD slot | $48 + $20 |
| Used 512 GB 2230 NVMe | Faster, roomier storage on the X1208 | $25–36 |
| Beitian BN-220 GPS module + jumper wires | Position and offline time for the maps | $12–15 |
| Micro-HDMI to HDMI panel-mount cable, 30 cm | A full-size HDMI port on the case | $10 |
| Raspberry Pi RTC battery | Clock survives with the battery out | $5 *list* |
| M2.5 standoffs, heat-set inserts | Mounting | $15 |

## AI board upgrades

Details and sources: [research/ai-upgrade.md](research/ai-upgrade.md).

| Option | Cost | What it buys | Catch |
|---|---|---|---|
| Better models on the 4 GB board | $0 | Qwen3-1.7B as the default, Qwen3-4B for hard questions, answers grounded in the offline library | Still small models, about 3–8 tokens/s |
| **Used Pi 5 16 GB**, sell the 4 GB | about $135–190 asking, minus ~$70–90 for the 4 GB | A 30B-class model at about 8 tokens/s; drop-in, every Pi part still fits | Depends on finding one |
| Radxa ROCK 5C 16 GB | $160 official, often sold out | About twice the Pi 5's speed on 3B models; the 30B model would likely run faster than on a Pi | Not a Pi: the display, battery board and parts of the setup scripts need replacing or porting |

## Don't buy

| Part | Why not |
|---|---|
| New Pi 5 16 GB ($305–350) or 8 GB ($200) | Used 16 GB boards and the ROCK 5C cost far less for the same or better result |
| Raspberry Pi AI HAT+ 2 ($130) | Slower than the Pi's own CPU at language models in independent tests |
| M5Stack AI-8850 accelerator kit ($185–215) | Vendor's own figure is 15 tokens/s on a 1.5B model, barely above the Pi's ~10 |
| Orange Pi 5 Pro or Max 16 GB ($350–400) | Same RK3588 chip as the ROCK 5C at more than twice the price |
| Jetson Orin Nano Super ($399) | Fast, but only 8 GB of memory, larger, and its price rose from $249 |
| New 1 TB NVMe ($150–250) | Used 512 GB drives cost a sixth as much |
| M.2 HAT+ Compact | Not compatible with the Active Cooler |

## What the budget build gives up

- **Battery integration.** The power bank rides on a strap or in a pocket on a short cable. It has no
  safe-shutdown signal, so the Pi cannot see its charge or power off cleanly when it runs dry.
- **Speed and space.** The microSD and USB stick are slower than NVMe and hold less. Fine for
  reading, films and the library; slower for big installs.
- **A built-in HDMI port.** The cable plugs into the Pi's micro-HDMI port directly until the case gets
  a panel port.

## The keyboard compromise

- A full key set this compact has to fold. The tri-fold lies flat on a table or thigh, which also avoids
  the hinged-screen balance problem builders keep reporting.
- A slide-out keyboard can only be as wide as the slab, about 150 mm, so it would be a 40 % layout with
  numbers on a second layer. That is a custom build for later, only if the tri-fold falls short.

## Risks to check when parts arrive

- **Power bank output.** It must offer 5 V / 3 A over USB-C PD. The Pi then limits USB ports to 600 mA,
  which is fine for a Bluetooth keyboard and a USB stick.
- **Video.** The Pi 5 decodes HEVC in hardware up to 4K, but H.264 only in software, fine at 1080p.
  Keep films in HEVC.
- **Screen size.** 720p on 5" needs about 1.5x scaling. Heavy work goes to the TV over HDMI.

## Sources (checked 2026-10-17/18)

- Raspberry Pi 5 16 GB at $305: [raspberrypi.com](https://www.raspberrypi.com/products/raspberry-pi-5/).
  8 GB at $200: [Adafruit](https://www.adafruit.com/product/5813). Street prices and used asking prices:
  [DEV price history](https://dev.to/revenueclaw/raspberry-pi-5-price-history-how-far-have-prices-come-187h),
  [camelcamelcamel](https://camelcamelcamel.com/product/B0F6L766R9).
- ROCK 5C 16 GB at $159.99: [Allnet China](https://shop.allnetchina.cn/products/rock-5c).
  RK3588 llama.cpp numbers: [Turing Pi](https://turingpi.com/llm-inference-benchmarks-rk3588-gguf-quantization/).
- AI-8850 kit: [CNX Software](https://www.cnx-software.com/2026/01/31/24-tops-m5stack-ai-8850-llm-accelerator-m-2-kit-offers-an-alternative-to-raspberry-pi-ai-hat-2/),
  [M5Stack store](https://shop.m5stack.com/products/ai-8850-llm-acceleration-m-2-kit-4gb-version-ax8850).
- Orange Pi 5 Max 16 GB: [orangepi.net](https://orangepi.net/product/orange-pi-5-max-16gb-ram).
  Jetson Orin Nano Super at $399: [ComputingForgeeks](https://computingforgeeks.com/edge-llm-jetson-orin-vs-ai-hat-2-vs-hailo-10h/).
- Flash prices: [Yahoo Finance](https://finance.yahoo.com/sectors/technology/articles/memory-card-prices-jump-124-150718829.html),
  [PCWorld FIT Plus deal](https://www.pcworld.com/article/2777956/score-samsungs-ultra-tiny-128gb-flash-drive-for-only-15.html),
  [eBay used 512 GB 2230 example](https://www.ebay.com.au/itm/198535452797).
- Touch Display 2, 5-inch: [It's FOSS](https://itsfoss.com/news/raspberry-pi-touch-display-2/).
  Geekworm X1208: [geekworm.com](https://geekworm.com/en-au/products/x1208).
  AI HAT+ 2 benchmarks: [CNX Software](https://www.cnx-software.com/2026/01/20/raspberry-pi-ai-hat-2-review-a-40-tops-ai-accelerator-tested-with-computer-vision-llm-and-vlm-workloads/).
