#!/usr/bin/env bash
# 30-network: unilateral ad blocking and the firewall (docs/04-privacy-adblock.md).
#   - NetworkManager stops managing resolv.conf; resolv.conf points at 127.0.0.1
#   - Blocky (filtering resolver, DoT upstreams, OISD + HaGeZi lists) on 127.0.0.1:53
#   - nftables: default-deny inbound, every DNS query redirected to Blocky, DoT/DoH bypasses dropped
#   - Wi-Fi MAC randomization
#   --test runs the acceptance checks instead of provisioning.
#
# Resolver choice: Blocky because its whole config is one YAML file in git and it starts with no
# wizard. AdGuard Home is the alternative when a web UI is wanted (decision 0005).
. "$(dirname "$0")/../lib.sh"
stage_begin 30-network
require_root

BLOCKY_VERSION="${POCKET_BLOCKY_VERSION:-v0.26.2}"   # newer releases: github.com/0xERR0R/blocky/releases
# sha256 of blocky_<version>_Linux_arm64.tar.gz, from the release's checksums file. Another version needs its own
# value in POCKET_BLOCKY_SHA256; the download is refused without a matching checksum.
BLOCKY_SHA256="${POCKET_BLOCKY_SHA256:-}"
[ -n "$BLOCKY_SHA256" ] || [ "$BLOCKY_VERSION" != v0.26.2 ] || BLOCKY_SHA256=7b22fa3c51fc372fcb9592437ab0e8ea2508592a8359c56fec99804cfcbfda0d
[ -n "$BLOCKY_SHA256" ] || die "no checksum known for blocky $BLOCKY_VERSION: set POCKET_BLOCKY_SHA256"

if [ "${1:-}" = "--test" ]; then
  ensure_pkg dnsutils curl
  fail=0
  log "1. a hard-coded resolver gets redirected"
  if dig +short +time=3 @8.8.8.8 pagead2.googlesyndication.com | grep -qx '0.0.0.0'; then log "   PASS"; else warn "   FAIL"; fail=1; fi
  log "2. DoH to a public resolver is blocked"
  if curl -s -m 5 'https://dns.google/resolve?name=example.com' >/dev/null; then warn "   FAIL (DoH reachable)"; fail=1; else log "   PASS"; fi
  log "3. resolv.conf is ours"
  if grep -qx 'nameserver 127.0.0.1' /etc/resolv.conf; then log "   PASS"; else warn "   FAIL"; fail=1; fi
  log "4. blocky answers and blocks"
  if dig +short +time=3 @127.0.0.1 pagead2.googlesyndication.com | grep -q '^0\.0\.0\.0$'; then log "   PASS"; else warn "   FAIL"; fail=1; fi
  log "5. normal names resolve"
  if dig +short +time=3 @127.0.0.1 debian.org | grep -qE '^[0-9]'; then log "   PASS"; else warn "   FAIL"; fail=1; fi
  log "(hotspot test is manual: connect a phone and nslookup ads.doubleclick.net)"
  [ "$fail" = 0 ] && log "all local checks passed" || die "some checks failed"
  exit 0
fi

ensure_pkg nftables curl ca-certificates dnsutils

# --- resolver user and binary -----------------------------------------------------------------
if ! id blocky >/dev/null 2>&1; then run useradd --system --no-create-home --shell /usr/sbin/nologin blocky; fi
if [ ! -x /usr/local/bin/blocky ] || ! /usr/local/bin/blocky version 2>/dev/null | grep -q "${BLOCKY_VERSION#v}"; then
  log "installing blocky $BLOCKY_VERSION"
  tmp="$(mktemp -d)"
  run curl -fsSL -o "$tmp/blocky.tar.gz" \
    "https://github.com/0xERR0R/blocky/releases/download/${BLOCKY_VERSION}/blocky_${BLOCKY_VERSION}_Linux_arm64.tar.gz"
  [ "$DRY_RUN" = 1 ] || echo "$BLOCKY_SHA256  $tmp/blocky.tar.gz" | sha256sum -c --quiet || die "blocky checksum failed"
  run tar -xzf "$tmp/blocky.tar.gz" -C "$tmp" blocky
  run install -m 0755 "$tmp/blocky" /usr/local/bin/blocky
  rm -rf "$tmp"
fi
install_etc etc/blocky/config.yml
install_etc etc/blocky/custom-deny.txt
install_etc etc/blocky/custom-allow.txt
install_etc etc/systemd/system/blocky.service
run chown -R blocky:blocky /etc/blocky

# --- DNS ownership: NetworkManager hands off, resolv.conf is a plain file we control ------------
install_etc etc/NetworkManager/conf.d/pocket.conf
if mountpoint -q /etc/resolv.conf 2>/dev/null; then
  warn "/etc/resolv.conf is a mount (container build); leaving it alone"
else
  if [ -L /etc/resolv.conf ]; then backup_once /etc/resolv.conf; run rm -f /etc/resolv.conf; fi
  install_etc etc/resolv.conf
fi
if systemctl is-active --quiet systemd-resolved 2>/dev/null; then
  warn "systemd-resolved is active; its stub on 127.0.0.53 is harmless but disable it if port 53 conflicts"
fi

# --- start the resolver before the firewall so lookups never go dark ---------------------------
svc daemon-reload
svc enable --now blocky.service
svc restart blocky.service      # pick up config changes on re-runs; cheap on a fresh install
svc reload NetworkManager || true
[ "$DRY_RUN" = 1 ] || sleep 4   # lists load before queries are answered (strategy: blocking)

# --- firewall ---------------------------------------------------------------------------------
install_etc etc/nftables.conf
if [ "$DRY_RUN" != 1 ]; then
  if out="$(nft -c -f /etc/nftables.conf 2>&1)"; then
    log "nftables.conf parses"
  elif printf '%s' "$out" | grep -qi 'netlink'; then
    warn "cannot validate nftables.conf here (no netlink: container or chroot); it will be checked on the device"
  else
    printf '%s\n' "$out" >&2; die "nftables.conf failed to parse"
  fi
fi
svc enable --now nftables.service
svc reload nftables.service

if command -v dig >/dev/null 2>&1 && systemd_running; then
  log "resolver: $(dig +short +time=3 @127.0.0.1 debian.org 2>/dev/null | head -1 || echo 'no answer yet')"
fi
warn "run 'sudo ./run.sh 30 -- --test' for the acceptance checks; hotspot: 'nmcli dev wifi hotspot ifname ap0 ssid <name> password <password>' after creating ap0 (see docs/research/open-questions.md)"
stage_end
