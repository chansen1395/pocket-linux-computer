# Runbook 00 — Flash the microSD from the Windows PC with no card reader

The Pi 5 can expose its own microSD (and NVMe) to a PC as a USB disk. The PC then writes the OS
image with Raspberry Pi Imager and the Pi reboots into it. Needs: a USB-C cable that carries data,
a USB port on the PC that carries data (rear motherboard ports are the safe choice), the `rpiboot`
host tool, and Raspberry Pi Imager 2.0.6 or newer.

Status: worked on 2026-10-16 (rpiboot windows-v1.1, Imager 2.0.8, image 2026-10-06 Trixie). The Pi was
not seen by the PC on front-panel USB ports; a rear motherboard port with a data cable worked.

## Host preparation (once)

1. Install `rpiboot` from the usbboot releases (`rpiboot_setup.exe`). It installs to
   `C:\Program Files (x86)\Raspberry Pi\` with the `mass-storage-gadget64` payload and the WinUSB driver.
2. Install Raspberry Pi Imager (`winget install RaspberryPiFoundation.RaspberryPiImager`).
3. Download the image (`https://downloads.raspberrypi.com/raspios_arm64_latest`) and check its `.sha256`.
4. Write the first-boot files (Trixie uses cloud-init): `user-data` (hostname, user with password hash
   and SSH key, `enable_ssh: true`) and `network-config` (Wi-Fi with `regulatory-domain`). Copy
   `flash-kit/user-data.example` and `flash-kit/network-config.example` and fill them in. The filled-in files
   hold your Wi-Fi password and keys: keep them out of version control (the kit `.gitignore` does).

## Steps

1. Start the host tool first; it waits:
   ```
   cd "C:\Program Files (x86)\Raspberry Pi" && rpiboot.exe -d mass-storage-gadget64
   ```
2. Put the Pi into USB device mode: unplug it completely, press and **hold** the power button, plug the
   USB-C cable into the PC while holding, release about a second after it is in. Only the red LED lights.
3. `rpiboot` prints `Second stage boot server done`, and a ~64 GB USB disk appears in Windows
   (`Get-Disk`), plus a `USB Serial Device (COMx)`: a root shell on the gadget with no password.
   If Windows offers to format the disk, cancel.
4. Flash, elevated:
   ```
   rpi-imager --cli --cloudinit-userdata user-data --cloudinit-networkconfig network-config <image>.img.xz \\.\PhysicalDriveN
   ```
   Imager verifies the write. Afterwards the FAT `bootfs` partition is visible in Windows; check that
   `user-data` and `network-config` are on it.
5. Reboot the Pi into the new card without touching it: open the COM port at any baud and type
   `reboot`. Or unplug and power it from the real supply.
6. Within ~3 minutes the Pi joins Wi-Fi under the hostname you set (`pocket` in the example) and
   `ssh <user>@pocket.local` works with the key you put in `user-data`.

## Troubleshooting

- Nothing appears on the PC and no Windows PnP event: the port or cable has no data lines, or the
  button hold was not caught. Try a rear USB port, a cable known to sync a phone, and release the
  button sooner.
- `rpiboot` sees the device but no disk appears: run it again with `-d mass-storage-gadget64`
  explicitly, and check Device Manager for a driver problem on "BCM2712 Boot".
- Powered from a PC port, the Pi 5 reports under-voltage but runs; keep it headless and avoid heavy
  loads until it is on a real supply.
