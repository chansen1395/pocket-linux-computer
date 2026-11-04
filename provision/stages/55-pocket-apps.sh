#!/usr/bin/env bash
# 55-pocket-apps: install the device software from this repo: pocket_core (device backend, `pocketctl` CLI,
# `pocket-mcp` MCP server) and Pocket TUI (console UI) into one venv, expose them in ~/.local/bin,
# register the MCP server with Claude Code, and make console mode launch Pocket TUI.
. "$(dirname "$0")/../lib.sh"
stage_begin 55-pocket-apps
require_root
[ -n "$POCKET_HOME" ] || die "cannot find the home directory of $POCKET_USER"

ensure_pkg python3 python3-venv python3-pip
repo="$(cd "$POCKET_ROOT/.." && pwd)"
venv="$POCKET_HOME/.venvs/pocket"

[ -d "$venv" ] || { log "creating venv $venv"; as_user python3 -m venv "$venv"; }
as_user "$venv/bin/pip" install -q --upgrade pip
for pkg in core tui; do
  if [ -f "$repo/$pkg/pyproject.toml" ]; then
    log "installing $pkg"
    as_user "$venv/bin/pip" install -q -e "$repo/$pkg"
  else
    warn "$repo/$pkg has no pyproject.toml; skipped"
  fi
done

as_user mkdir -p "$POCKET_HOME/.local/bin"
for b in pocketctl pocket-mcp pocket-tui; do
  [ -x "$venv/bin/$b" ] && as_user ln -sf "$venv/bin/$b" "$POCKET_HOME/.local/bin/$b"
done

# Privileged writes pocket_core makes (power profile, snapshots) go through pocket-helper, which checks every
# argument against an exact allow-list. The only other rules are fixed commands with no wildcard.
install_helper
core_sudoers="$(mktemp)"
cat > "$core_sudoers" <<EOF
$POCKET_USER ALL=(root) NOPASSWD: /usr/local/bin/pocket-mode
$POCKET_USER ALL=(root) NOPASSWD: /usr/bin/systemctl reboot, /usr/bin/systemctl poweroff
EOF
if visudo -cf "$core_sudoers" >/dev/null; then
  cmp -s "$core_sudoers" /etc/sudoers.d/pocket-core || run install -m 0440 "$core_sudoers" /etc/sudoers.d/pocket-core
else
  warn "pocket-core sudoers snippet failed validation; the desktop, reboot and power-off buttons will report an error"
fi
rm -f "$core_sudoers"

# Claude Code: register the MCP server at user scope (idempotent).
if [ -x "$POCKET_HOME/.local/bin/claude" ] && [ -x "$POCKET_HOME/.local/bin/pocket-mcp" ]; then
  if ! as_user bash -lc 'claude mcp get pocket' >/dev/null 2>&1; then
    as_user bash -lc "claude mcp add --scope user pocket -- $POCKET_HOME/.local/bin/pocket-mcp" \
      || warn "could not register the MCP server; later: claude mcp add --scope user pocket -- ~/.local/bin/pocket-mcp"
  fi
fi

# Console mode runs Pocket TUI inside tmux.
if [ -x "$POCKET_HOME/.local/bin/pocket-tui" ] && [ -f /etc/systemd/system/pocket-console.service ]; then
  if ! grep -q 'bin/pocket-tui' /etc/systemd/system/pocket-console.service; then
    run sed -i "s|-e tmux new -A -s pocket$|-e tmux new -A -s pocket $POCKET_HOME/.local/bin/pocket-tui|" /etc/systemd/system/pocket-console.service
    svc daemon-reload
  fi
fi

if [ -x "$venv/bin/pocketctl" ]; then as_user "$venv/bin/pocketctl" status || warn "pocketctl status failed"; fi
stage_end
