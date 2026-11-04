#!/usr/bin/env bash
# 70-knowledge: offline library (docs/03-ai-integration.md §5). Installs kiwix-serve on 127.0.0.1:8090
# and downloads the ZIM files listed in config/knowledge/manifest.txt into /data/kiwix.
# Big downloads: run on a fast link; re-running resumes and skips what is present.
. "$(dirname "$0")/../lib.sh"
stage_begin 70-knowledge
require_root

ensure_pkg kiwix-tools curl
run mkdir -p /data/kiwix && run chown "$POCKET_USER:$POCKET_USER" /data/kiwix
install_etc etc/systemd/system/kiwix.service
run sed -i "s|@USER@|$POCKET_USER|g" /etc/systemd/system/kiwix.service

base="https://download.kiwix.org/zim"
while read -r folder prefix _; do
  [ -z "$folder" ] && continue; case "$folder" in \#*) continue;; esac
  latest="$(curl -fsSL "$base/$folder/" | grep -oE "${prefix}_[0-9]{4}-[0-9]{2}\.zim" | sort -u | tail -1 || true)"
  if [ -z "$latest" ]; then warn "no file matching $prefix in $base/$folder/"; continue; fi
  if [ -e "/data/kiwix/$latest" ]; then log "present: $latest"; continue; fi
  log "downloading $latest"
  as_user curl -fL --retry 5 -C - -o "/data/kiwix/$latest.part" "$base/$folder/$latest" && run mv "/data/kiwix/$latest.part" "/data/kiwix/$latest"
done < "${POCKET_MANIFEST:-$POCKET_CONFIG/knowledge/manifest.txt}"

as_user bash -c 'cd /data/kiwix && rm -f library.xml && for z in *.zim; do kiwix-manage library.xml add "$z"; done' || true
svc daemon-reload
svc enable --now kiwix.service
log "library: http://127.0.0.1:8090"
stage_end
