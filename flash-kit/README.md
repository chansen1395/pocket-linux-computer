# flash-kit: write Raspberry Pi OS to the Pi 5's own microSD from a Windows PC

This writes Raspberry Pi OS plus your first-boot settings onto a microSD card while the card sits inside
the Pi 5, using the Pi's USB mass-storage mode. No card reader is needed. It is the procedure described in
[runbook 00](../provision/runbooks/00-flash-from-pc.md); the scripts here do the two Windows-side steps.

It worked once, on one Windows 10 PC, on 2026-10-16. Read `flash.ps1` before running it: it writes to a disk.
It refuses to run unless exactly one USB or SD disk of roughly 64 GB is attached, so a card of another size
needs an edit to the size check.

## You provide

| File | What |
|---|---|
| `*.img.xz` | the Raspberry Pi OS image (64-bit, Trixie), from https://www.raspberrypi.com/software/operating-systems/; check its `.sha256` |
| `user-data` | first-boot settings: hostname, user, SSH key. Start from `user-data.example` |
| `network-config` | your Wi-Fi. Start from `network-config.example` |

The last two hold secrets. `.gitignore` keeps them out of git; keep them out of everything else you share.

## Needs on the PC

- `rpiboot` (usbboot), installed to `C:\Program Files (x86)\Raspberry Pi\` with the `mass-storage-gadget64` payload.
- Raspberry Pi Imager 2.0.6 or newer, at `C:\Program Files\Raspberry Pi Ltd\Imager\rpi-imager.exe`.
- A USB-C cable that carries data, and a USB port that carries data (a rear motherboard port is the safe choice).

## Steps

1. Double-click `1-start-usb-mode.cmd`. A window opens and waits for the Pi.
2. Put the Pi in USB mode: unplug all power (a shutdown is not enough), press and hold the Pi's power
   button, plug the USB-C cable into the PC while holding, release about a second later. Only the red LED
   should be on. The window from step 1 ends with `Second stage boot server done`. If Windows offers to
   format the disk, cancel.
3. Double-click `2-flash.cmd` and accept the administrator prompt. It finds the disk, refuses anything that
   is not exactly one ~64 GB USB disk, writes and verifies the image (5 to 10 minutes) and logs to `flash.log`.
4. Unplug the Pi from the PC and power it from its proper supply. A Pi powered only from a PC port may
   report low voltage.
5. After 2 to 3 minutes the Pi joins your Wi-Fi under the hostname in `user-data`. Continue with
   [runbook 10](../provision/runbooks/10-first-contact.md).

If step 2 never shows the Pi, try the other rear port, a different cable, and releasing the button sooner.
As a last resort, put the card in a reader: `2-flash.cmd` works the same way.
