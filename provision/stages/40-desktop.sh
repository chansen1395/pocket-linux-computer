#!/usr/bin/env bash
# 40-desktop: the two modes and the apps (docs/02-software.md).
# Assumes the full Raspberry Pi OS image (labwc desktop present). On Lite, install the desktop
# first: sudo apt install raspberrypi-ui-mods, then re-run.
#   - Firefox from the Pi repo + policies (telemetry off, DoH off and locked, uBlock Origin forced)
#   - VSCodium from its apt repo (Claude Code extension is on Open VSX)
#   - foot, cage, mpv, yt-dlp, fonts; Textual for Pocket TUI development
#   - pocket-mode: switch between console (cage kiosk) and desktop (lightdm)
. "$(dirname "$0")/../lib.sh"
stage_begin 40-desktop
require_root

run apt-get update
ensure_pkg firefox foot cage mpv yt-dlp fonts-jetbrains-mono fonts-noto-color-emoji \
           wl-clipboard wtype brightnessctl pipx python3-dev

# --- Firefox policies (both locations, depending on how the package is built) --------------------
install_etc etc/firefox/policies/policies.json
if [ -d /usr/lib/firefox ]; then
  run mkdir -p /usr/lib/firefox/distribution
  if ! cmp -s "$POCKET_CONFIG/etc/firefox/policies/policies.json" /usr/lib/firefox/distribution/policies.json 2>/dev/null; then
    run install -m 0644 "$POCKET_CONFIG/etc/firefox/policies/policies.json" /usr/lib/firefox/distribution/policies.json
  fi
fi

# --- VSCodium ----------------------------------------------------------------------------------
if ! command -v codium >/dev/null 2>&1; then
  log "adding the VSCodium apt repo"
  run bash -c "curl -fsSL https://gitlab.com/paulcarroty/vscodium-deb-rpm-repo/raw/master/pub.gpg | gpg --dearmor -o /usr/share/keyrings/vscodium-archive-keyring.gpg"
  ensure_line /etc/apt/sources.list.d/vscodium.list "deb [signed-by=/usr/share/keyrings/vscodium-archive-keyring.gpg] https://download.vscodium.com/debs vscodium main"
  run apt-get update
  ensure_pkg codium
fi
# Claude Code extension from Open VSX (idempotent; codium exits 0 if already installed)
as_user codium --install-extension anthropic.claude-code --force >/dev/null 2>&1 || warn "could not install the Claude Code extension; try from the VSCodium UI (Open VSX)"

# --- yt-dlp: Debian's package is months old and YouTube changes often; keep a current one via pipx ----
as_user pipx install yt-dlp >/dev/null 2>&1 || as_user pipx upgrade yt-dlp >/dev/null 2>&1 || warn "pipx yt-dlp install failed; the apt version stays"
as_user pipx ensurepath >/dev/null 2>&1 || true

# --- modes ---------------------------------------------------------------------------------------
install_etc usr/local/bin/pocket-mode 0755
install_etc etc/systemd/system/pocket-console.service
run sed -i "s|@USER@|$POCKET_USER|g" /etc/systemd/system/pocket-console.service
svc daemon-reload
# Backlight control without sudo for the user (brightnessctl uses the video group).
run usermod -aG video,input "$POCKET_USER"

warn "modes: 'sudo pocket-mode console' / 'sudo pocket-mode desktop'. Console mode opens a plain terminal until stage 55 installs the Pocket TUI."
stage_end
