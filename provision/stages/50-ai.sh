#!/usr/bin/env bash
# 50-ai: Claude Code on the device, with a safety net (docs/03-ai-integration.md).
#   - Claude Code via the native installer, installed as the user (never as root)
#   - tmux so sessions survive the screen and the phone link
#   - hooks: snapshot before risky commands, audit log of every command
#   - pocket-helper: the user may take, and delete, the hook's btrfs snapshots without a password (nothing else)
. "$(dirname "$0")/../lib.sh"
stage_begin 50-ai
require_root
[ -n "$POCKET_HOME" ] || die "cannot find the home directory of $POCKET_USER"

ensure_pkg jq tmux git curl ca-certificates

# --- Claude Code (native installer; Debian arm64 is an officially supported platform) ------------
if [ ! -x "$POCKET_HOME/.local/bin/claude" ]; then
  log "installing Claude Code for $POCKET_USER"
  as_user bash -c 'curl -fsSL https://claude.ai/install.sh | bash'
else
  log "Claude Code present: $(as_user "$POCKET_HOME/.local/bin/claude" --version 2>/dev/null || echo '?')"
fi
ensure_line "$POCKET_HOME/.profile" 'export PATH="$HOME/.local/bin:$PATH"'
run chown "$POCKET_USER:$POCKET_USER" "$POCKET_HOME/.profile"

# --- hooks and settings ---------------------------------------------------------------------------
install_etc usr/local/bin/pocket-snapshot 0755
install_etc usr/local/bin/pocket-audit 0755
install_home .claude/settings.json
install_home .tmux.conf
run mkdir -p "$POCKET_HOME/.pocket"
run chown -R "$POCKET_USER:$POCKET_USER" "$POCKET_HOME/.pocket" "$POCKET_HOME/.claude"

# --- snapshots without a password, through pocket-helper only (exact name patterns, no sudoers wildcard) ----
install_helper

if [ "$(findmnt -no FSTYPE /)" = "btrfs" ]; then
  run mkdir -p /.snapshots
else
  warn "root is not btrfs: the snapshot hook will quietly do nothing until runbook 20 is done"
fi

warn "next, as $POCKET_USER: run 'claude' once and sign in with the Claude subscription; then 'tmux new -s claude'"
stage_end
