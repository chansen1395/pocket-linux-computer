#!/usr/bin/env bash
# Shared helpers for Pocket provisioning. Sourced by run.sh and by every stage.
# Rule: every helper is idempotent. Running a stage twice must change nothing the second time.

set -euo pipefail

POCKET_ROOT="${POCKET_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
POCKET_CONFIG="$POCKET_ROOT/config"
POCKET_STATE="/var/lib/pocket"
# The user the stages act for: POCKET_USER, else the user who ran sudo. No default user name is assumed.
POCKET_USER="${POCKET_USER:-${SUDO_USER:-}}"
POCKET_HOME=""
[ -z "$POCKET_USER" ] || POCKET_HOME="$(getent passwd "$POCKET_USER" 2>/dev/null | cut -d: -f6 || true)"
BOOT_CONFIG="${BOOT_CONFIG:-/boot/firmware/config.txt}"
DRY_RUN="${DRY_RUN:-0}"

log()  { printf '\033[1;32m[pocket]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[pocket] warning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[pocket] error:\033[0m %s\n' "$*" >&2; exit 1; }

# run CMD... : execute, or under DRY_RUN=1 only print.
run() {
  if [ "$DRY_RUN" = 1 ]; then printf '  would run: %s\n' "$*"; else "$@"; fi
}

require_root() { [ "$(id -u)" -eq 0 ] || die "run this with sudo"; }

require_pi5() {
  if ! grep -q "Raspberry Pi 5" /proc/device-tree/model 2>/dev/null; then
    [ "$DRY_RUN" = 1 ] && { warn "not a Raspberry Pi 5 (dry run, continuing)"; return 0; }
    [ "${POCKET_SKIP_HW_CHECK:-0}" = 1 ] && { warn "not a Raspberry Pi 5 (POCKET_SKIP_HW_CHECK=1, continuing)"; return 0; }
    die "this is not a Raspberry Pi 5"
  fi
}

# systemd_running : true when a live systemd manages this system (false in a container or chroot build).
systemd_running() { [ -d /run/systemd/system ] && [ "${SYSTEMCTL_OFFLINE:-0}" != 1 ]; }

# svc ACTION [--now] UNIT... : systemctl that degrades gracefully without a running systemd:
# enable/disable/mask still work offline (symlinks only); start/stop/reload/daemon-reload are skipped.
svc() {
  local action="$1"; shift
  local now=0 a args=()
  for a in "$@"; do if [ "$a" = "--now" ]; then now=1; else args+=("$a"); fi; done
  if systemd_running; then
    if [ "$now" = 1 ]; then run systemctl "$action" --now "${args[@]}"; else run systemctl "$action" "${args[@]}"; fi
    return
  fi
  case "$action" in
    enable|disable|mask|unmask)
      run env SYSTEMCTL_OFFLINE=1 systemctl "$action" "${args[@]}" || warn "offline systemctl $action ${args[*]} failed"
      [ "$now" = 1 ] && log "(no systemd running: not starting ${args[*]})"
      ;;
    *) log "(no systemd running: skipped systemctl $action ${args[*]})" ;;
  esac
  return 0
}

# set_hostname NAME : hostnamectl when systemd runs, plain files otherwise.
set_hostname() {
  if systemd_running; then run hostnamectl set-hostname "$1"; else
    if [ "$DRY_RUN" = 1 ]; then printf '  would write /etc/hostname: %s\n' "$1"; else printf '%s\n' "$1" > /etc/hostname; fi
  fi
  ensure_line /etc/hosts "127.0.1.1 $1"
}

# ensure_pkg PKG... : apt-install what is missing, nothing else.
ensure_pkg() {
  local missing=() p
  for p in "$@"; do dpkg -s "$p" >/dev/null 2>&1 || missing+=("$p"); done
  [ ${#missing[@]} -eq 0 ] && return 0
  log "installing: ${missing[*]}"
  run env DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 install -y --no-install-recommends "${missing[@]}"
}

# backup_once FILE : copy FILE to FILE.pocket.bak the first time we touch it.
backup_once() {
  if [ -e "$1" ] && [ ! -e "$1.pocket.bak" ]; then run cp -a "$1" "$1.pocket.bak"; fi
}

# ensure_line FILE LINE : append LINE unless an identical line already exists.
ensure_line() {
  local file="$1" line="$2"
  if grep -qxF -- "$line" "$file" 2>/dev/null; then return 0; fi
  backup_once "$file"
  if [ "$DRY_RUN" = 1 ]; then
    printf '  would append to %s: %s\n' "$file" "$line"
  else
    mkdir -p "$(dirname "$file")"
    printf '%s\n' "$line" >> "$file"
  fi
}

# set_config_txt KEY=VALUE : set a key in the [all] section of config.txt, replacing an existing value.
# For dtparam=X=Y the key is "dtparam=X". A bare "dtparam=X" or "dtoverlay=X" is appended as a line.
set_config_txt() {
  local kv="$1" key="${1%=*}"
  backup_once "$BOOT_CONFIG"
  if [ "$key" = "dtparam" ] || [ "$key" = "dtoverlay" ]; then ensure_line "$BOOT_CONFIG" "$kv"; return 0; fi
  if grep -qE "^${key}=" "$BOOT_CONFIG" 2>/dev/null; then
    grep -qxF -- "$kv" "$BOOT_CONFIG" && return 0
    log "config.txt: $kv"
    run sed -i -E "s|^${key}=.*|${kv}|" "$BOOT_CONFIG"
  else
    [ "$(grep -E '^\[' "$BOOT_CONFIG" 2>/dev/null | tail -1)" = "[all]" ] || ensure_line "$BOOT_CONFIG" "[all]"
    log "config.txt: $kv"
    ensure_line "$BOOT_CONFIG" "$kv"
  fi
}

# set_eeprom KEY=VALUE... : stage EEPROM bootloader settings (applied on the next reboot).
set_eeprom() {
  command -v rpi-eeprom-config >/dev/null 2>&1 || { warn "rpi-eeprom-config not installed; skipping EEPROM settings $*"; return 0; }
  local tmp changed=0 kv key
  tmp="$(mktemp)"
  rpi-eeprom-config > "$tmp" 2>/dev/null || { warn "rpi-eeprom-config cannot read the EEPROM here; skipping $*"; rm -f "$tmp"; return 0; }
  for kv in "$@"; do
    key="${kv%%=*}"
    if grep -qE "^${key}=" "$tmp"; then
      grep -qxF -- "$kv" "$tmp" || { sed -i -E "s|^${key}=.*|${kv}|" "$tmp"; changed=1; }
    else
      printf '%s\n' "$kv" >> "$tmp"; changed=1
    fi
  done
  if [ "$changed" = 1 ]; then
    log "EEPROM: $*"
    run rpi-eeprom-config --apply "$tmp"
    needs_reboot "EEPROM settings: $*"
  else
    log "EEPROM already set: $*"
  fi
  rm -f "$tmp"
}

# install_etc etc/PATH [MODE] : copy config/etc/PATH to /etc/PATH if it differs (config/ mirrors /).
install_etc() {
  local mode="${2:-0644}" src="$POCKET_CONFIG/$1" dst="/$1"
  [ -e "$src" ] || die "missing config file $src"
  if [ -e "$dst" ] && cmp -s "$src" "$dst"; then return 0; fi
  backup_once "$dst"
  log "installing $dst"
  run install -D -m "$mode" "$src" "$dst"
}

# install_home PATH [MODE] : copy config/home/PATH into the user's home as PATH, owned by the user.
install_home() {
  local mode="${2:-0644}" src="$POCKET_CONFIG/home/$1" dst="$POCKET_HOME/$1"
  [ -e "$src" ] || die "missing config file $src"
  if [ -e "$dst" ] && cmp -s "$src" "$dst"; then return 0; fi
  log "installing $dst"
  run install -D -m "$mode" -o "$POCKET_USER" -g "$POCKET_USER" "$src" "$dst"
}

# install_helper : install pocket-helper (root-owned) and let POCKET_USER run exactly that program through sudo.
# The helper validates its own arguments against an exact allow-list, so no sudoers wildcard is needed.
install_helper() {
  install_etc usr/local/bin/pocket-helper 0755
  local tmp; tmp="$(mktemp)"
  printf '%s ALL=(root) NOPASSWD: /usr/local/bin/pocket-helper\n' "$POCKET_USER" > "$tmp"
  if visudo -cf "$tmp" >/dev/null; then
    cmp -s "$tmp" /etc/sudoers.d/pocket-helper 2>/dev/null || run install -m 0440 "$tmp" /etc/sudoers.d/pocket-helper
  else
    warn "pocket-helper sudoers rule failed validation; power profile and snapshot writes will report ok=false"
  fi
  rm -f "$tmp"
  run rm -f /etc/sudoers.d/pocket-snapshots   # an older rule with a wildcard, if an earlier version of the stages made it
}

# as_user CMD... : run a command as the invoking user with a login-like environment.
as_user() { run sudo -u "$POCKET_USER" -H env HOME="$POCKET_HOME" "$@"; }

# wait_cool [MAX_C] [MAX_SECONDS] : pause until the SoC is below MAX_C (default 65) or the time is up.
# Use before benchmarks and other all-core loads; a bare Pi 5 with no cooler hits its soft limit in minutes.
wait_cool() {
  local max="${1:-65}" limit="${2:-180}" t=0 c
  command -v vcgencmd >/dev/null 2>&1 || return 0
  while [ "$t" -lt "$limit" ]; do
    c="$(vcgencmd measure_temp 2>/dev/null | tr -dc '0-9.' | cut -d. -f1)"
    [ -n "$c" ] && [ "$c" -lt "$max" ] && return 0
    [ "$t" = 0 ] && log "waiting for the SoC to cool below ${max} C (now ${c:-?} C)"
    sleep 10; t=$((t + 10))
  done
  warn "still ${c:-?} C after ${limit} s; continuing"
}

needs_reboot() {
  [ "$DRY_RUN" = 1 ] && return 0
  mkdir -p "$POCKET_STATE"
  printf '%s\n' "$1" >> "$POCKET_STATE/needs-reboot"
}

require_user() {
  [ -n "$POCKET_USER" ] || die "set POCKET_USER to the account to provision (or run through sudo)"
  [[ "$POCKET_USER" =~ ^[a-z_][a-z0-9_-]*$ ]] || die "POCKET_USER '$POCKET_USER' is not a plain account name"
}

stage_begin() {
  STAGE_NAME="$1"; log "=== stage $STAGE_NAME ==="
  require_user
  [ "$DRY_RUN" = 1 ] || mkdir -p "$POCKET_STATE/stages"
}
stage_end()   { [ "$DRY_RUN" = 1 ] || date -Is > "$POCKET_STATE/stages/$STAGE_NAME"; log "=== stage $STAGE_NAME done ==="; }
