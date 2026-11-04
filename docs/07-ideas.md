# 07 — Ideas

A running list of features beyond the MVP, each with the phase it belongs to and the hardware it
needs. "Novel" here means: not something a phone or a laptop already does better. Promote an idea
by giving it a decision file and a stage.

| # | Idea | Why it matters in a go-bag | Needs | Phase |
|---|---|---|---|---|
| 1 | **Field Agent recipes.** Claude Code slash commands that drive the device through the pocket MCP server: `/sitrep` (status, position, battery hours, messages), `/hotspot`, `/endurance`, `/backup now`, `/fix-wifi`, `/find <thing> nearby` (offline map POIs). Voice later. | The point of an AI with grippers is that you say what you want, not how. | core + MCP | 2 |
| 2 | **Question inbox with sync-later.** Ask anything while offline; the local model answers now (marked "local, low confidence"); when a link returns, the queue goes to Claude and the better answer lands next to the first. Also stores every Claude answer for offline re-reading. | Off-grid you still get an answer, and you never lose the good one. | local model | 2 |
| 3 | **Pocket Portal.** When the hotspot is up, anyone who joins gets a page: the offline library, maps, a local message board, a file drop, and "ask the Pi". A disaster-relief info kiosk in a pocket. | A single device helps a whole group, with phones they already have. | hotspot | 2 |
| 4 | **One-cable laptop mode.** Plug the device into any laptop over USB-C: it appears as a USB network card, so the laptop's screen and keyboard drive the device over SSH or the Portal. | Borrowed laptop, no Wi-Fi, no monitor: still full access. | `rpi-usb-gadget` (Trixie ships it) | 1 |
| 5 | **Physical safe-mode switch.** `config.txt` conditional sections (`[gpio21=0]`) pick a rescue `os_prefix` or a no-services cmdline when a slide switch is set, so a bad provisioning run can never brick the device. | The AI can experiment hard because recovery is a switch, not a reflash. | one switch on GPIO | 2 |
| 6 | **Situational awareness tab.** Position, heading, sunrise/sunset, moon phase, barometric trend ("pressure falling 4 hPa/3 h: storm likely"), cached forecast, nearest cached water/shelter/hospital POIs from the offline map. | A field computer's real job. Works with no signal. | GPS, BME280 | 2–3 |
| 7 | **Document vault.** Photograph IDs, prescriptions, insurance, deeds with the camera; OCR with tesseract; store `age`-encrypted on `/data`; search by text. | The papers you grab in a fire, already in the bag. | camera | 3 |
| 8 | **Radio scanner presets.** RTL-SDR with `rtl_fm` profiles: NOAA weather, FM, aviation, FRS/GMRS, marine, and ham repeaters chosen from an offline directory by GPS position. | Information when the internet is gone. | RTL-SDR | 3 |
| 9 | **Power-aware scheduler.** Heavy jobs (backups, ZIM refresh, model downloads, nightly Claude maintenance) run only on charger and Wi-Fi; endurance mode shows hours remaining from measured consumption, not a guess. | Battery is the real budget. | UPS board | 2 |
| 10 | **Panic wipe.** Hold two buttons five seconds, confirm on screen: the LUKS key slot for `/data` is destroyed. Data is unrecoverable; the OS still boots. | Protects the data on a lost or stolen device. | LUKS (decision 0006) | 3 |
| 11 | **Voice memos to markdown.** whisper.cpp transcribes recordings into dated notes; synced to another machine; searchable in Pocket TUI. | Captures notes without typing. | mic | 2 |
| 12 | **Self-knowledge.** The repo, runbooks and decisions live on the device and are indexed with the library, so the local model can explain how to fix the device itself with no internet. | The manual is inside the machine. | local model | 2 |
| 13 | **Peer sync.** Two devices, or a device and a home server, exchange notes, maps and messages over the hotspot or LoRa when they meet. | Sneakernet for families and teams. | Syncthing, Meshtastic | 3 |
| 14 | **Ask the library.** Local embeddings over WikiMed, the survival PDFs and your own notes; answers with citations from the local model. | Medical questions with no signal. | local model | 3 |
| 15 | **Weather station.** BME280 log, 72-hour pressure chart, storm warning thresholds. | Cheap and always on. | BME280 | 2 |
| 16 | **QR everything.** Camera reads Wi-Fi QR codes to join networks, scans documents, reads Meshtastic channel QRs. | Zero typing on a tiny keyboard. | camera | 3 |
| 17 | **E-ink status tag.** A 2.9" e-ink on the cradle showing battery, position, unread messages, next check-in; refreshed by a timer at microwatts. | Glanceable with the main screen off for days. | e-ink HAT | 4 |
| 18 | **Check-in beacon.** Scheduled "I'm OK at <position>" via Meshtastic, email or Matrix, with a cancel button; log synced home. | Lets people stop worrying. | radio or LTE | 3 |
| 19 | **Ham/GMRS companion.** Band plans, repeater directory, logbook, with the SDR as a receiver. License first. | The classic emergency comms stack. | SDR | 3 |
| 20 | **Game Boy on the go.** mGBA through RetroArch in desktop mode; the "Radio" tab gets a "Games" sibling. | Entertainment; the lowest priority. | none | 3 |
| 21 | **TV mode.** Plug into a hotel TV: HDMI hot-plug starts Kodi full-screen on the SSD's media, the TV remote drives it over HDMI-CEC, unplugging returns to the tiles. | Your films anywhere, no streaming account. | HDMI panel port | 2 |
| 22 | **Hotel mode.** Log into the hotel's captive portal once on the device, then share that connection through its hotspot to the phone and laptop, with ad blocking applied to every device. | One login, private and ad-free for everything you carry. | stage 30 + hotspot test | 2 |
| 23 | **GPS time.** chrony fed by gpsd keeps the clock accurate with no internet, for logs, sunrise times and two-factor codes. | Correct time when everything else is down. | GPS | 2 |
| 24 | **HF email and chat.** Winlink email and JS8Call keyboard chat over a ham radio through a Digirig interface. License first. | The emcomm use the ham community relies on when cell networks fail. | radio + Digirig | 3 |
| 25 | **Swappable cells.** Carry charged 21700s as spare batteries; the fuel gauge tile shows hours left from measured draw. | Runtime without a big, heavy battery. | X1208 | 2 |

## Principles for picking

- Prefer features that work with **no signal** over features that need one.
- Prefer features that **other people** benefit from (Portal, peer sync, hotspot) over single-user polish.
- Every feature is a power cost first; measure before shipping.
- Nothing here changes the phase-1 hardware.
