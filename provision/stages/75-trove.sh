#!/usr/bin/env bash
# 75-trove: download the offline content pack (config/knowledge/trove-manifest.txt) into /data.
# Research, licenses and the full list: docs/research/trove.md.
#   POCKET_TROVE_FILTER='kiwix|docs/medical'   regex matched against "<dest> <name>"; default everything
#   POCKET_TROVE_MAX_MB=25000                  skip any item that would push the planned total past this (0 = no cap)
#   POCKET_TROVE_VERIFY=1                      re-hash files that are already present
# Resumable (curl -C -), checksum-verified when the manifest has a sha256, safe to re-run.
. "$(dirname "$0")/../lib.sh"
stage_begin 75-trove
require_root
ensure_pkg curl ca-certificates

manifest="${POCKET_TROVE_MANIFEST:-$POCKET_CONFIG/knowledge/trove-manifest.txt}"
filter="${POCKET_TROVE_FILTER:-.}"
cap="${POCKET_TROVE_MAX_MB:-25000}"
[ -r "$manifest" ] || die "no manifest at $manifest"
run mkdir -p /data
run chown "$POCKET_USER:$POCKET_USER" /data

planned=0 got=0 present=0 skipped=0 failed=0
while IFS=$'\t' read -r url dest size sha name; do
  [ -z "$url" ] && continue
  case "$url" in \#*) continue ;; esac
  printf '%s %s\n' "$dest" "$name" | grep -Eq "$filter" || continue
  size_int="${size%%.*}"; size_int="${size_int:-0}"
  if [ "$cap" != 0 ] && [ $((planned + size_int)) -gt "$cap" ]; then
    warn "budget of $cap MB reached; skipping $name ($size MB)"; skipped=$((skipped + 1)); continue
  fi
  planned=$((planned + size_int))
  target="/data/$dest"
  if [ -s "$target" ]; then
    if [ "$sha" != "-" ] && [ "${POCKET_TROVE_VERIFY:-0}" = 1 ]; then
      if echo "$sha  $target" | sha256sum -c --quiet 2>/dev/null; then present=$((present + 1)); continue; fi
      warn "checksum mismatch, re-downloading $name"
    else
      present=$((present + 1)); continue
    fi
  fi
  log "downloading $name ($size MB) -> $dest"
  [ "${POCKET_TROVE_DELAY:-0}" = 0 ] || sleep "$POCKET_TROVE_DELAY"   # be polite to small servers; some reject a fast burst
  run mkdir -p "$(dirname "$target")"
  run chown "$POCKET_USER:$POCKET_USER" "$(dirname "$target")"
  if as_user curl -fL --retry 5 --retry-delay 10 -C - -A "Mozilla/5.0 (X11; Linux aarch64) Pocket" -o "$target.part" "$url"; then
    if [ "$DRY_RUN" != 1 ] && [ "$sha" != "-" ] && ! echo "$sha  $target.part" | sha256sum -c --quiet 2>/dev/null; then
      warn "checksum FAILED for $name; kept as $target.part"; failed=$((failed + 1)); continue
    fi
    run mv "$target.part" "$target"; got=$((got + 1))
  else
    warn "download failed: $name"; failed=$((failed + 1))
  fi
done < "$manifest"
log "trove: $got downloaded, $present already present, $skipped over budget, $failed failed; planned $planned MB"

# ZIMs land in /data/kiwix: refresh the library so kiwix-serve sees them.
if command -v kiwix-manage >/dev/null 2>&1 && ls /data/kiwix/*.zim >/dev/null 2>&1; then
  as_user bash -c 'cd /data/kiwix && rm -f library.xml && for z in *.zim; do kiwix-manage library.xml add "$z" >/dev/null; done'
  svc restart kiwix.service
fi
stage_end
