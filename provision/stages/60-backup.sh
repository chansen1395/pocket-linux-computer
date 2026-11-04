#!/usr/bin/env bash
# 60-backup: restic to a repository you configure, Syncthing for live folders.
# Configure the destination in /etc/pocket/restic.env (copied from the example) before the timer does anything.
. "$(dirname "$0")/../lib.sh"
stage_begin 60-backup
require_root

ensure_pkg restic syncthing
svc enable --now "syncthing@${POCKET_USER}.service"

run mkdir -p /etc/pocket
install_etc etc/pocket/restic.env.example 0600
[ -e /etc/pocket/restic.env ] || warn "copy /etc/pocket/restic.env.example to restic.env and fill it in; the timer skips until then"
install_etc usr/local/bin/pocket-backup 0755
install_etc etc/systemd/system/pocket-backup.service
install_etc etc/systemd/system/pocket-backup.timer
svc daemon-reload
svc enable --now pocket-backup.timer
log "syncthing UI: http://127.0.0.1:8384 (as $POCKET_USER); backup timer: $(systemctl list-timers pocket-backup.timer --no-legend 2>/dev/null | head -1)"
stage_end
