# 00 — Vision

## One sentence

A go-bag computer: grab it and leave the laptop behind, and still have a full Linux
machine with a keyboard, a screen, terabytes of storage, days of battery, offline
knowledge, and an AI that can operate the machine for you whenever there is a signal.

## Who it is for

One builder, one device. Not a product. That changes the trade-offs: we can accept
quirks that a product could not, and we can rebuild the whole thing from a script.

## Scenarios it must handle

1. **Daily carry.** On a belt loop or in a bag. Pull it out, check mail, read, write
   code, talk to Claude, play a film on a train. Charges from any USB-C PD brick.
2. **Laptop left behind.** A week away with only this. SSH to a home server, edit a repo
   in VS Code, run Claude Code against it, browse without ads, print nothing.
3. **Off-grid.** No internet for days. Offline Wikipedia, maps with GPS, medical and
   repair references, ebooks, music, films, a local small language model for the basics,
   text messaging over LoRa mesh to other nodes, radio listening via SDR. Solar charging.
4. **Lost or stolen.** Data at rest encrypted; API sessions revocable; nothing on it that
   cannot be revoked or rebuilt.

## Hard requirements

- Raspberry Pi 5, 4 GB. (Design must not preclude swapping in the 8/16 GB board.)
- 1 TB storage minimum, 2 TB target.
- Physical keyboard and a touchscreen; usable standing up, one-handed for simple things.
- Battery: a working day of mixed use. Charge over USB-C PD, including from a solar panel.
- Claude Code, VS Code (or VSCodium), and the Claude web app in a browser, all on the device.
- Ad blocking at the DNS level for most apps on every network, without the builder thinking about it.
- No Chrome. No telemetry we did not choose. Local-first everything.
- Wearable: forearm cradle, belt-loop clip, bag sleeve, all from one core unit.
- 3D-printed enclosure we design and can re-print after every iteration.

## Explicit non-goals (for now)

- Phone replacement (calls, SMS). Tethering to the phone is fine.
- Gaming as a priority. Emulators come after the MVP and must not shape the hardware.
- Waterproofing. Splash resistance via gaskets is a stretch goal.
- Selling it.

## Principles

- **Iterate, don't marry.** Every choice is written down as a decision that can be
  superseded. When a ready-made part is almost right and cannot be bent, we build.
- **The repo is the device.** `provision/` rebuilds the Pi from a fresh image. Manual
  tweaks get folded back in or they are lost on purpose.
- **Safe to let an AI drive.** Snapshots before changes, a rescue microSD always in the
  slot, a hardware watchdog, and a documented rollback for every stage.
- **Power is the real budget.** Every feature is costed in watts before it is costed in dollars.
- **Measure, then decide.** Runtime, thermals and RAM headroom get measured on the real
  board before any decision moves from *proposed* to *accepted*.

## References worth stealing from

- **Pilet 5 / Pilet 7** (SoulsCircuit): CM5-based handhelds, 5" with built-in keyboard or
  7" 1280×800 touch with a detachable keyboard or gamepad, ~7 h claimed, optional 8000 mAh
  module, ~$200–250 without the Pi. Closest thing to this project that you can buy.
- **Clockwork uConsole**: CM4, 5" screen, 18650 cells, the best-executed "handheld Linux" form factor.
- **MNT Pocket Reform**: open-hardware 7" mini laptop; its mechanical keyboard design is a model for ours.
- **r/cyberDeck and cyberdeck.cafe**: thousands of one-off builds, many with Pi 5 power and thermal data.
