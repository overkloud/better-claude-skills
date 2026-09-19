# tools

Command-line tools and scripts for working with Claude Code. Everything in
[`bin/`](bin/) is an executable that `install.sh` puts on your `PATH`.

Requires macOS. Logs go to `~/.log/`.

## Install

```sh
git clone https://github.com/overkloud/better-claude-skills.git
cd better-claude-skills
tools/install.sh
```

This copies every tool into `~/.local/bin`, creates `~/.log/`, and prints
anything left to do by hand: a `PATH` line if needed, and the hooks to paste
into `~/.claude/settings.json`. It never edits your shell rc files or
settings, and it's safe to re-run.

| Flag | Effect |
|------|--------|
| `--bin-dir DIR` | Install somewhere other than `~/.local/bin` |
| `--link` | Symlink into the checkout instead of copying, so `git pull` updates the tools |
| `--uninstall` | Remove the tools this checkout installed; any other file is left alone |

## Tools

### `claude-sessions`

Snapshots the Claude Code sessions you have open and reopens them in iTerm2
after a reboot, crash or accidental quit. Each session goes back into its
original window and tab.

```sh
claude-sessions save               # snapshot running sessions
claude-sessions list               # show the snapshot
claude-sessions restore --dry-run  # print what restore would open
claude-sessions restore            # reopen everything that isn't already running
```

**Requires** iTerm2 and `jq` (bundled with recent macOS; otherwise `brew install jq`).

**Keep the snapshot current automatically** by adding these hooks to
`~/.claude/settings.json` (`install.sh` prints them with your install path filled in):

```json
"hooks": {
  "SessionStart": [{"matcher": "", "hooks": [{"type": "command", "command": "~/.local/bin/claude-sessions save --from-hook", "timeout": 10}]}],
  "SessionEnd":   [{"matcher": "", "hooks": [{"type": "command", "command": "~/.local/bin/claude-sessions save --from-hook", "timeout": 10}]}]
}
```

The snapshot is written to `~/.claude/session-snapshot.json`. A session that
is killed (tab closed, iTerm2 quit, reboot) leaves the snapshot untouched, so
it still holds what restore should bring back; a deliberate `/exit` drops that
session from it.

**Limits:** windows and tabs come back exactly. Split panes inside a tab are
best effort: iTerm2 doesn't expose pane positions, so split orientation is
inferred from pane sizes.

**Environment:**

| Variable | Default | Purpose |
|----------|---------|---------|
| `CLAUDE_CONFIG_DIR` | `~/.claude` | Claude Code config dir |
| `CLAUDE_SESSIONS_LOG` | `~/.log/claude-sessions.log` | Log file (rotated at 1 MB) |
| `CLAUDE_SESSIONS_DELAY` | `0.6` | Seconds between tab launches on restore |

When a save or restore misbehaves, check the log first. Every run is logged,
including hook-driven ones.
