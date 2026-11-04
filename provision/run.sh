#!/usr/bin/env bash
# Pocket provisioning runner.
#
#   sudo ./run.sh --list            stages and when each last completed
#   sudo ./run.sh 10 30             run stages by number, in the order given
#   sudo ./run.sh all               run every stage in numeric order
#   sudo DRY_RUN=1 ./run.sh 30      print what a stage would change
#   sudo ./run.sh 30 -- --test      pass extra arguments to a stage
#
# Stages are stages/NN-name.sh. Each is idempotent and may request a reboot; the runner reports
# that at the end instead of rebooting for you.

set -euo pipefail
cd "$(dirname "$0")"
. ./lib.sh

usage() { sed -n '2,11p' "$0"; exit 1; }
[ $# -ge 1 ] || usage
require_root

list_stages() {
  local s name when
  for s in stages/[0-9][0-9]-*.sh; do
    name="$(basename "$s" .sh)"
    when="$(cat "$POCKET_STATE/stages/$name" 2>/dev/null || echo "never")"
    printf '  %-16s last completed: %s\n' "$name" "$when"
  done
}

if [ "$1" = "--list" ]; then list_stages; exit 0; fi

selected=() extra=()
if [ "$1" = "all" ]; then
  for s in stages/[0-9][0-9]-*.sh; do selected+=("$s"); done
  shift
else
  while [ $# -gt 0 ] && [ "$1" != "--" ]; do
    match=(stages/"$1"-*.sh)
    [ -e "${match[0]}" ] || die "no stage numbered $1"
    selected+=("${match[0]}"); shift
  done
fi
[ "${1:-}" = "--" ] && { shift; extra=("$@"); }

[ "$DRY_RUN" = 1 ] && log "DRY RUN: nothing will change"
for s in "${selected[@]}"; do
  bash "$s" "${extra[@]}"
done

# A reboot marker written before the last boot is stale: clear it.
if [ -e "$POCKET_STATE/needs-reboot" ] && [ "$(stat -c %Y "$POCKET_STATE/needs-reboot")" -lt "$(date -d "$(uptime -s)" +%s)" ]; then
  rm -f "$POCKET_STATE/needs-reboot"
fi
if [ -s "$POCKET_STATE/needs-reboot" ] 2>/dev/null; then
  warn "a reboot is needed for:"
  sed 's/^/    /' "$POCKET_STATE/needs-reboot"
  warn "run: sudo reboot"
fi
