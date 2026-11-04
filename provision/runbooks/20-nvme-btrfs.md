# Runbook 20 — Move the system to the NVMe with a btrfs root

**Status: drafted 2026-10-16 from the standard Raspberry Pi OS procedure, not yet executed.**
Run it from the rescue microSD system, with stages 10 and 20 already applied there and one
reboot done so PCIe is live. Budget an hour. Everything on the NVMe is destroyed.

Plan B, if btrfs fights back: skip steps 4–7, use `rpi-clone` (or the SD Card Copier in the
desktop) to copy the SD to the NVMe as ext4, and install `timeshift` in rsync mode for snapshots.

## Preflight

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT        # expect mmcblk0 (SD, booted) and nvme0n1 (empty)
findmnt /                                          # must be on mmcblk0p2, not the NVMe
rpi-eeprom-config | grep -E 'BOOT_ORDER|PCIE_PROBE' # 0xf416 and 1
dmesg | grep -i -E 'pcie|nvme' | tail             # link up; note the speed (2.5 or 5 or 8 GT/s)
```

## Steps

1. **Partition** the NVMe like the stock image: a 512 MiB FAT32 boot partition, the rest for root.
   ```bash
   sudo parted -s /dev/nvme0n1 mklabel gpt \
     mkpart bootfs fat32 4MiB 516MiB \
     mkpart rootfs btrfs 516MiB 100%
   sudo mkfs.vfat -F 32 -n BOOTFS /dev/nvme0n1p1
   sudo mkfs.btrfs -f -L ROOTFS /dev/nvme0n1p2
   ```
2. **Subvolumes.** Root in `@`, home in `@home`, so snapshots of the system do not drag home along.
   ```bash
   sudo mount /dev/nvme0n1p2 /mnt
   sudo btrfs subvolume create /mnt/@
   sudo btrfs subvolume create /mnt/@home
   sudo btrfs subvolume create /mnt/@snapshots
   sudo umount /mnt
   sudo mount -o subvol=@,compress=zstd:3,noatime /dev/nvme0n1p2 /mnt
   sudo mkdir -p /mnt/home /mnt/boot/firmware /mnt/.snapshots
   sudo mount -o subvol=@home,compress=zstd:3,noatime /dev/nvme0n1p2 /mnt/home
   sudo mount /dev/nvme0n1p1 /mnt/boot/firmware
   ```
3. **Copy** the running system (one filesystem at a time, preserving everything).
   ```bash
   sudo rsync -aHAXx --numeric-ids --info=progress2 --exclude=/home/* / /mnt/
   sudo rsync -aHAX --numeric-ids --info=progress2 /home/ /mnt/home/
   sudo rsync -aHAX --numeric-ids --info=progress2 /boot/firmware/ /mnt/boot/firmware/
   ```
4. **fstab** on the NVMe copy. Replace the two existing lines with:
   ```
   LABEL=ROOTFS  /               btrfs  defaults,noatime,compress=zstd:3,subvol=@      0 0
   LABEL=ROOTFS  /home           btrfs  defaults,noatime,compress=zstd:3,subvol=@home  0 0
   LABEL=ROOTFS  /.snapshots     btrfs  defaults,noatime,subvol=@snapshots             0 0
   LABEL=BOOTFS  /boot/firmware  vfat   defaults                                        0 2
   ```
   `sudoedit /mnt/etc/fstab`
5. **cmdline.txt** on the NVMe copy: change `root=PARTUUID=...` to
   `root=LABEL=ROOTFS rootfstype=btrfs rootflags=subvol=@` and keep `rootwait` and the rest on one line.
   `sudoedit /mnt/boot/firmware/cmdline.txt`
6. **initramfs** must know btrfs. Inside a chroot of the copy:
   ```bash
   for d in dev proc sys run; do sudo mount --bind /$d /mnt/$d; done
   sudo chroot /mnt bash -c 'grep -qx btrfs /etc/initramfs-tools/modules || echo btrfs >> /etc/initramfs-tools/modules; update-initramfs -u -k all'
   for d in run sys proc dev; do sudo umount /mnt/$d; done
   ```
   The Pi kernel builds btrfs as a module; the image uses `auto_initramfs=1`, so the regenerated
   initramfs is picked up from `/boot/firmware` automatically. **verify** on the first run.
7. **Unmount and reboot.** Leave the SD in. The EEPROM tries the NVMe first.
   ```bash
   sudo umount -R /mnt && sudo reboot
   ```

## Verify

```bash
findmnt -no SOURCE,FSTYPE,OPTIONS /      # /dev/nvme0n1p2[/@] btrfs ... subvol=/@
sudo btrfs subvolume list /              # @, @home, @snapshots
sudo btrfs scrub start -B /              # clean
sudo rpi-eeprom-update                   # up to date
sudo ./run.sh --list                     # stage markers came across with the copy
```

Then run `sudo ./run.sh 50` so the snapshot hooks activate, and take the first snapshot:
`sudo btrfs subvolume snapshot -r / /.snapshots/$(date +%F)-first-nvme-boot`.

## Rollback

Pull the ribbon or set `BOOT_ORDER=0xf41` temporarily (`sudo rpi-eeprom-config --edit`) and the
SD boots as before. Nothing on the SD was modified by this runbook.
