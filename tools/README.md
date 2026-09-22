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
original window, tab and split pane.

```sh
claude-sessions save               # snapshot running sessions
claude-sessions list               # show the snapshot
claude-sessions restore --dry-run  # print what restore would open
claude-sessions restore            # reopen everything that isn't already running
```

**Requires** iTerm2 with its Python API enabled (iTerm2 > Settings > General >
Magic > Enable Python API), [`uv`](https://docs.astral.sh/uv/) (`brew install uv`)
and `jq` (bundled with recent macOS; otherwise `brew install jq`). The layout
half lives in `claude-sessions-iterm`, a small Python script that `uv` runs
with the `iterm2` library; `install.sh` puts it next to `claude-sessions`.

**Upgrading from an earlier version:** the tool now needs `uv` and iTerm2's
Python API. Earlier versions drove iTerm2 through AppleScript, which cannot
tell where a split pane sits, so panes came back in the wrong order. Install
`uv`, enable the API in iTerm2's settings, and re-run `install.sh`; existing
hooks and snapshots keep working, and the next save records the full layout.

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

**Limits:** windows, tabs and split panes come back in their saved
arrangement, but every split is 50/50: pane sizes are not restored. A session
that wasn't in iTerm2 when saved (ssh, tmux) opens in a tab of its own.

**Environment:**

| Variable | Default | Purpose |
|----------|---------|---------|
| `CLAUDE_CONFIG_DIR` | `~/.claude` | Claude Code config dir |
| `CLAUDE_SESSIONS_LOG` | `~/.log/claude-sessions.log` | Log file (rotated at 1 MB) |
| `CLAUDE_SESSIONS_DELAY` | `0.6` | Seconds after each command sent on restore, so iTerm2 keeps up |

When a save or restore misbehaves, check the log first. Every run is logged,
including hook-driven ones.
