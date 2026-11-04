#!/usr/bin/env bash
# 20-storage: PCIe and NVMe boot settings only. Copying the system to the NVMe and converting
# it to btrfs are deliberate manual steps: see ../runbooks/20-nvme-btrfs.md.
#
#   POCKET_PCIE_GEN=2 (default) or 3. Gen 3 is faster and officially uncertified; earn it with a
#   week of stable Gen 2 first (decision 0002).
. "$(dirname "$0")/../lib.sh"
stage_begin 20-storage
require_root; require_pi5

gen="${POCKET_PCIE_GEN:-2}"
case "$gen" in 2|3) ;; *) die "POCKET_PCIE_GEN must be 2 or 3";; esac

# Enable the PCIe connector (HAT+ boards enable it themselves; harmless to state it) and the link speed.
set_config_txt "dtparam=pciex1"
set_config_txt "dtparam=pciex1_gen=$gen"
needs_reboot "PCIe settings (gen $gen)"

# Boot order, read right to left: 6 = NVMe, 1 = SD card, 4 = USB, f = start again.
# PCIE_PROBE=1 lets the bootloader look for NVMe on boards that are not HAT+.
set_eeprom BOOT_ORDER=0xf416 PCIE_PROBE=1

# --- report ---------------------------------------------------------------------------------
if command -v nvme >/dev/null 2>&1 && nvme list 2>/dev/null | grep -q /dev/nvme; then
  log "NVMe devices:"; nvme list
  nvme smart-log /dev/nvme0 2>/dev/null | grep -E 'temperature|percentage_used|data_units' || true
else
  warn "no NVMe visible. Expected on the first run before a reboot; otherwise check the ribbon and the board."
fi
log "block devices:"; lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT
log "root filesystem: $(findmnt -no SOURCE,FSTYPE /)"

if [ "$(findmnt -no FSTYPE /)" != "btrfs" ]; then
  warn "root is not btrfs yet. Snapshots (stage 50 hooks) stay disabled until runbooks/20-nvme-btrfs.md is done."
fi

stage_end
