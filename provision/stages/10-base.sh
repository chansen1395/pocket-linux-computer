#!/usr/bin/env bash
# 10-base: the boring foundation. Packages, hostname, zram, watchdog, RTC battery charging,
# power-off-on-halt, SSH (keys only, and only once a key exists), /data.
. "$(dirname "$0")/../lib.sh"
stage_begin 10-base
require_root; require_pi5

# --- hostname -------------------------------------------------------------------------------
want="${POCKET_HOSTNAME:-pocket}"
if [ "$(hostname)" != "$want" ]; then
  log "hostname -> $want"
  set_hostname "$want"
fi

# --- SSH policy first: key-only login, so a freshly installed sshd never comes up accepting passwords -------
install_etc etc/ssh/sshd_config.d/00-pocket.conf

# --- packages -------------------------------------------------------------------------------
# PackageKit refreshes lists in the background on a fresh desktop image; wait for the lock instead of failing.
ensure_line /etc/apt/apt.conf.d/99pocket-lock 'DPkg::Lock::Timeout "600";'
run apt-get -o DPkg::Lock::Timeout=600 update
ensure_pkg sudo openssh-server git tmux mosh curl wget jq vim htop usbutils i2c-tools \
           btrfs-progs nftables unattended-upgrades rpi-eeprom \
           python3 python3-pip python3-venv pipx gnupg pass age \
           smartmontools nvme-cli bc

# --- zram: compressed swap in RAM; the cheapest way to stretch 4 GB ----------------------------
# Raspberry Pi OS Trixie already runs a zram swap (50 % of RAM); zram-tools would fight it for /dev/zram0.
if grep -q zram /proc/swaps 2>/dev/null; then
  log "zram swap already active: $(awk '/zram/{print $1, int($3/1024) " MB"}' /proc/swaps | head -1)"
  if dpkg -s zram-tools >/dev/null 2>&1; then
    svc disable --now zramswap.service || true
    run env DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 -y purge zram-tools
  fi
else
  ensure_pkg zram-tools
  backup_once /etc/default/zramswap
  run sed -i -E 's|^#?\s*ALGO=.*|ALGO=zstd|; s|^#?\s*PERCENT=.*|PERCENT=50|' /etc/default/zramswap
  svc enable --now zramswap.service
fi

# --- persistent journal: the image keeps logs in RAM, so a crash takes its own evidence with it ---
if [ ! -d /var/log/journal ]; then
  run mkdir -p /var/log/journal
  run systemd-tmpfiles --create --prefix /var/log/journal
  svc restart systemd-journald || true
fi

# --- hardware watchdog: a hang becomes a reboot, not a brick in a bag --------------------------
set_config_txt "dtparam=watchdog=on"
install_etc etc/systemd/system.conf.d/pocket-watchdog.conf

# --- RTC: trickle-charge the coin cell so the clock survives days without power -----------------
set_config_txt "dtparam=rtc_bbat_vchg=3000000"

# --- power: allow full USB current on a 3 A bank; halt means a real power-off ------------------
set_config_txt "usb_max_current_enable=1"
set_eeprom POWER_OFF_ON_HALT=1

# --- updates: security only, never kernel or firmware by surprise ------------------------------
ensure_line /etc/apt/apt.conf.d/20auto-upgrades 'APT::Periodic::Update-Package-Lists "1";'
ensure_line /etc/apt/apt.conf.d/20auto-upgrades 'APT::Periodic::Unattended-Upgrade "1";'

# --- SSH: enabled only once the account has an authorized key; never with passwords -----------------
# The drop-in above sets PasswordAuthentication no. Without a key nobody could log in over SSH anyway, so the
# service stays off instead of listening for nothing (the firewall also accepts port 22 on every interface).
if [ -s "$POCKET_HOME/.ssh/authorized_keys" ]; then
  svc enable --now ssh
  svc reload ssh
else
  warn "no $POCKET_HOME/.ssh/authorized_keys: sshd is NOT enabled. Add your public key there and re-run stage 10."
  svc disable --now ssh || true
fi

# --- /data: where the big stuff lives; becomes the LUKS mount point in decision 0006 ------------
run mkdir -p /data/kiwix /data/media /data/maps /data/backups
run chown -R "$POCKET_USER:$POCKET_USER" /data
run mkdir -p "$POCKET_STATE"

stage_end
