# Is a bigger Pi worth it for a smarter AI? (checked 2026-10-17, cost update 2026-10-18)

## Cost update, 2026-10-18

New-board prices are high, so the ranking is by cost:

| Rank | Option | Net cost | Result | Catch |
|---|---|---|---|---|
| 1 | Better models on the 4 GB board | $0 | Qwen3-1.7B default, Qwen3-4B for hard questions (about 3 tok/s, estimate), answers grounded in Kiwix search results | Small models |
| 2 | **Used Pi 5 16 GB**, sell the 4 GB | about $50–120 after the sale | Qwen3-30B-A3B at about 8 tok/s; drop-in | Used asking prices seen at $135–190 ([eBay examples](https://www.ebay.de/itm/286278364686), [camelcamelcamel low $186](https://camelcamelcamel.com/product/B0F6L766R9)); the 4 GB sells new for about $96 ([DEV price history](https://dev.to/revenueclaw/raspberry-pi-5-price-history-how-far-have-prices-come-187h)) |
| 3 | Radxa ROCK 5C 16 GB | $160 ([Allnet China](https://shop.allnetchina.cn/products/rock-5c), sold out when checked) | RK3588S2 with about twice the Pi 5's memory bandwidth: Llama 3.2 3B at 11.25 tok/s on RK3588 ([Turing Pi](https://turingpi.com/llm-inference-benchmarks-rk3588-gguf-quantization/)) against about 4.8 on a Pi 5 | Not a Pi: the Touch Display 2, the X1208 and Pi-specific setup steps (EEPROM, config.txt, PMIC readings) need replacing or porting; no published Qwen3-30B number on RK3588 |

Passed over on price: the M5Stack AI-8850 accelerator kit at $185–215, whose vendor figure is 15 tok/s
on Qwen2.5-1.5B ([CNX Software](https://www.cnx-software.com/2026/01/31/24-tops-m5stack-ai-8850-llm-accelerator-m-2-kit-offers-an-alternative-to-raspberry-pi-ai-hat-2/));
Orange Pi 5 Pro and Max 16 GB at $350–400 ([orangepi.net](https://orangepi.net/product/orange-pi-5-max-16gb-ram));
the Jetson Orin Nano Super, now $399 for 8 GB ([ComputingForgeeks](https://computingforgeeks.com/edge-llm-jetson-orin-vs-ai-hat-2-vs-hailo-10h/)).

**Recommendation:** do rank 1 now, and watch for a used 16 GB Pi 5 under about $180.

---

The original analysis follows.

**Bottom line.** The competent AI on this device is Claude over the internet; the local model is the
offline fallback. If you upgrade, the only step worth paying for is the **16 GB Pi 5 ($305)**, which runs
a 30B-class model offline at about 8 tokens/s. Skip the AI HAT+ 2 and the 8 GB board. The 4 GB board
is fine until then: it measured 3.5 GB free at rest and runs a 1.5B model at about 10 tokens/s.

## Options

| Option | Cost | Best offline model it runs | Speed | Verdict |
|---|---|---|---|---|
| Keep the Pi 5 4 GB | $0 | Qwen2.5-1.5B (installed) | ~10 tok/s | Good for summaries and short answers; weak reasoning |
| Pi 5 8 GB | $200 | 4B models (Gemma 3 4B, Qwen3-4B) | ~3–6 tok/s | Small step, big price |
| **Pi 5 16 GB** | **$305** | **Qwen3-30B-A3B** (mixture of experts, 3B active) | **~8 tok/s** at 2.70 bits/weight, ~6.7 at 3.25 | **The real jump**; also makes desktop + VS Code + Firefox comfortable |
| AI HAT+ 2 (Hailo-10H, 8 GB on board) | $130 | 1–3B models from Hailo's zoo | 5.9–8.1 tok/s on 1.5B, slower than the CPU's 9–12 | Skip for language models; it also takes the PCIe lane the SSD needs |
| Compute Module 5 16 GB on a custom carrier | board design project | same as 16 GB | same | Most compact, but a PCB project; the Pilet handheld switched to CM5 and still has not shipped |

## The numbers behind it

- **Pi 5 16 GB, Qwen3-30B-A3B-Instruct-2507.** ByteShape's 2.70 bits-per-weight quant runs at 8.03 tok/s
  and keeps 94.18 % of full-precision quality; the 3.25 bpw quant runs at 6.68 tok/s and keeps 97.97 %
  ([ByteShape](https://byteshape.com/blogs/Qwen3-30B-A3B-Instruct-2507/)). Independent runs agree: 7.99 tok/s
  generation ([geerlingguy/ai-benchmarks #47](https://github.com/geerlingguy/ai-benchmarks/issues/47)),
  6–7 tok/s with a 4096-token context ([Hacker News](https://news.ycombinator.com/item?id=46520373)).
  File: `byteshape/Qwen3-30B-A3B-Instruct-2507-GGUF`, `...-Q3_K_S-2.70bpw.gguf`, about 10 GB
  (computed: 30.5 B weights × 2.70 bits). That leaves 4–5 GB for the system, so desktop apps must be
  closed while it runs.
- **Pi 5 8 GB, 4B models.** Reports for Gemma 3 4B range from 3.9 to 5.3 tok/s, with one outlier at
  8–11 ([kunalganglani.com](https://www.kunalganglani.com/blog/gemma-3-raspberry-pi-5-benchmark.md),
  [raspberry.tips](https://raspberry.tips/raspberrypi-tutorials/ollama-raspberry-pi-5)).
- **AI HAT+ 2.** CNX measured the Pi 5 CPU at 9–12 tok/s on 1.5B models against 5.9–8.1 on the HAT,
  and 4.8 against 2.6 on Llama 3.2 3B ([CNX Software](https://www.cnx-software.com/2026/01/20/raspberry-pi-ai-hat-2-review-a-40-tops-ai-accelerator-tested-with-computer-vision-llm-and-vlm-workloads/)).
  ComputingForgeeks found the CPU won every row across five models
  ([ComputingForgeeks](https://computingforgeeks.com/edge-llm-jetson-orin-vs-ai-hat-2-vs-hailo-10h/)).
  The HAT's real strengths are a fast first token (0.3–0.7 s), freeing the CPU, and camera vision work.
  Vendor-linked pages claiming 10x speedups could not be reproduced by these reviewers.
- **Prices.** 16 GB $305 on the [official page](https://www.raspberrypi.com/products/raspberry-pi-5/);
  8 GB $200 at [Adafruit](https://www.adafruit.com/product/5813); five increases since October 2025, driven
  by LPDDR4 ([The Register](https://www.theregister.com/2026/02/02/raspberry_pi_ram_shortage_price_hike/)).

## What a 30B model changes offline

- Answers and summaries from the Kiwix library (WikiMed, iFixit, survival manuals) with far fewer
  confident mistakes than a 1.5B model. Still verify medical answers against the source article.
- Usable help with code, shell commands and repairs to the device itself when there is no signal.
- Drafting messages and notes at reading speed (8 tok/s is about 6 words a second).

## Power and heat

All-core inference is the heaviest load the board sees. On the 900 mA phone charger it cut power twice
(2026-10-16). A 16 GB board running a 30B model needs the 27 W supply or the X1208's 5 A output, plus
the Active Cooler. On one 21700 cell, expect roughly 1.5 hours of continuous inference (estimate).

## If you buy it

The 16 GB board drops into the same enclosure; only RAM changes. Provisioning stage 80 gets a
`POCKET_LLM=qwen3-30b` option that downloads the ByteShape file when free RAM allows. The 4 GB board
then becomes a fixed Meshtastic base station or a home-server helper.
