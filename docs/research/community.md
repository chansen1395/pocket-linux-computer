# What people actually do with cyberdecks, and what goes wrong (checked 2026-10-17)

Reddit blocks automated search, so this draws on the ClockworkPi uConsole forum (the largest community
running a Pi-class handheld daily), Hackaday and Hackaday.io build logs, and project write-ups.
These are individual reports, not a survey.

## Real uses, most common first

| Use | Who reports it | Pocket status |
|---|---|---|
| SSH and terminal admin, light coding | uConsole owners: "ideal for public transport, hilltops and other situations where a laptop is a pain" | Done: Claude Code, tmux, mosh, VSCodium |
| Offline reference (Wikipedia, medical, repair) | Offline-platform projects | Done: 42 Kiwix archives, 112 documents |
| Off-grid text messaging over LoRa (Meshtastic, MeshCore) | Many 2025–26 builds | Planned: SPI LoRa HAT, phase 2 |
| Radio listening with an RTL-SDR (scanner, aircraft, weather satellites) | Ham and prepper decks | Planned: phase 3 |
| Ham radio digital modes: HF email (Winlink), keyboard chat (JS8Call), FT8 | Ham-focused decks; needs a license | New idea (07-ideas #24) |
| GPS logging and offline maps | Field-tool decks | GPS module on the shopping list |
| Writing without distractions ("writerdeck") | A recognized sub-genre | Works today in console mode |
| Network diagnostics, Wi-Fi auditing | Security-minded decks | Possible, not a goal |
| Media and retro games on the go | Common, rarely the main use | HDMI TV mode (07-ideas #21) |

A recurring framing: a cyberdeck is a field tool "not meant to be a substitute for your laptop"
([SpecFive](https://specfive.com/blogs/articles/handheld-linux-cyberdeck)). The builds people keep using are
the ones that do something a phone cannot: radios, offline knowledge, a real keyboard and shell.

## What goes wrong

| Problem | Evidence | What Pocket does about it |
|---|---|---|
| Battery life | uConsole owners report 1.5 h of hard work to 7–8 h idle, depending on the cells; the screen is the main drain on most builds | Small 5" screen, dimming in console mode, swappable 21700 cells, measured power numbers |
| Cheap cells | Builders insist on new, brand-name cells because of fire risk | Brand-name cells from a battery specialist (08-shopping-list) |
| Battery drains while off | A UPS board leaked 5–10 mA with everything off, emptying a 3000 mAh pack in weeks | Pull the cell for storage; measure the X1208's standby drain |
| Heat softens PLA cases | A printed PLA case failed from exhaust heat under load | PETG or ASA only (decision 0007); Active Cooler |
| Weight | Batteries dominate; heavy builds stay home | One cell, about 400 g target |
| Screen-and-keyboard balance | Hinged screens flop backwards unless the keyboard is weighted, which adds bulk | Separate fold-out keyboard that lies flat; slab on a strap or a kickstand |
| Keyboard ergonomics | uConsole owners like the keys but often plug in an external keyboard for long sessions; the trackball divides opinion | Full-size tri-fold for real typing; touchscreen for pointing |
| Stability on early hardware | Crashes, broken audio, 60–70 °C on CM4 uConsoles | Measured thermals, watchdog, snapshots, rebuild from scripts |
| Fuel gauges lie | A uConsole gauge read 100 % long before the cells were full | Calibrate against measured runtime before trusting "hours left" |

## Takeaways for the design

1. Optimize for the offline and radio uses; they are what keeps a deck out of the drawer.
2. Treat battery weight and screen power as the main budget, not CPU.
3. Keep the keyboard separate and flat rather than hinged to the screen.
4. Pull or switch off the cell for storage, and buy cells from a specialist.

## Sources

- [uConsole first impressions after a day of heavy use](https://forum.clockworkpi.com/t/first-impressions-after-a-day-of-heavy-use/12589),
  [uConsole battery life thread](https://forum.clockworkpi.com/t/battery-life-how-to-get-most-out-of-battery/16048),
  [uConsole review notes](https://forum.clockworkpi.com/t/uconsole-notes-for-review/12403),
  [hashbangcode CM4 review](https://www.hashbangcode.com/article/clockwork-pi-uconsole-cm4-review),
  [M0MNF CM5 and RF board review](https://m0mnf.com/reviews/uconsole.php)
- Hackaday: [At last, a cyberdeck you might want to use](https://hackaday.com/2022/05/31/at-last-a-cyberdeck-you-might-want-to-use/),
  [Making an ultra minimal cyberdeck](https://hackaday.com/2026/06/19/making-an-ultra-minimal-cyberdeck/),
  [2023 Cyberdeck Challenge](https://hackaday.com/tag/2023-cyberdeck-challenge/),
  [Hamdeck](https://hackaday.io/project/191890-hamdeck-cyberdeck)
- [SpecFive: handheld Linux cyberdeck](https://specfive.com/blogs/articles/handheld-linux-cyberdeck),
  [therustyrobot/cyberdeck](https://github.com/therustyrobot/cyberdeck),
  [Liliputing on the Pilet's switch to CM5](https://liliputing.com/tag/pilet-7/)
