#!/usr/bin/env bash
# install.sh — install every executable in tools/bin/ into your bin dir.
#
#   tools/install.sh [--link] [--bin-dir DIR]
#   tools/install.sh --uninstall [--bin-dir DIR]
#
#   --bin-dir DIR  where the tools go (default ~/.local/bin)
#   --link         symlink into this checkout instead of copying, so `git pull` updates them
#   --uninstall    remove the tools this checkout installed; any other file is left alone
#
# Safe to re-run. Never edits shell rc files or ~/.claude/settings.json; it
# prints what to add instead.

set -euo pipefail
unset CDPATH   # with it set, `cd relative/dir` can land elsewhere and echo the path into $(...)

die() { printf 'install.sh: %s\n' "$*" >&2; exit 1; }
usage() { sed -n '2,/^$/s/^# \{0,1\}//p' "${BASH_SOURCE[0]}"; }

# No `readlink -f` on macOS; cd + pwd -P finds the checkout from any cwd.
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/bin"
BIN_DIR="$HOME/.local/bin"
LINK=0 UNINSTALL=0

while [ $# -gt 0 ]; do
  case $1 in
    --bin-dir)   [ $# -ge 2 ] || die "--bin-dir needs a directory"; BIN_DIR=$2; shift ;;
    --link)      LINK=1 ;;
    --uninstall) UNINSTALL=1 ;;
    -h|--help)   usage; exit 0 ;;
    *)           usage >&2; die "unknown option: $1" ;;
  esac
  shift
done

# Every executable in tools/bin is a tool, so a new one needs no change here.
TOOLS=()
for f in "$SRC_DIR"/*; do
  [ -f "$f" ] && [ -x "$f" ] || continue
  TOOLS+=("${f##*/}")
done
[ ${#TOOLS[@]} -gt 0 ] || die "no executables in $SRC_DIR"

# ~/.log is where the tools write their logs by default.
[ "$UNINSTALL" = 1 ] || mkdir -p "$BIN_DIR" "$HOME/.log"
[ -d "$BIN_DIR" ] || { echo "nothing to uninstall: no $BIN_DIR"; exit 0; }
BIN_DIR=$(cd "$BIN_DIR" && pwd)   # absolute: it goes into the hook command below
# Installing or uninstalling onto the source dir would delete the repo's own files.
[ "$(cd "$BIN_DIR" && pwd -P)" != "$SRC_DIR" ] || die "--bin-dir is this repo's tools/bin"

if [ "$UNINSTALL" = 1 ]; then
  for t in "${TOOLS[@]}"; do
    dest=$BIN_DIR/$t
    # -L first: -f and cmp follow links, and a link to somewhere else is not ours
    # even when the file it points at happens to match.
    if [ -L "$dest" ]; then
      [ "$(readlink "$dest")" = "$SRC_DIR/$t" ] || { echo "kept    $dest (links elsewhere)"; continue; }
    elif [ -f "$dest" ]; then
      cmp -s "$dest" "$SRC_DIR/$t" || { echo "kept    $dest (not this checkout's copy)"; continue; }
    else
      continue
    fi
    rm -f "$dest"
    echo "removed $dest"
  done
  exit 0
fi

for t in "${TOOLS[@]}"; do
  # rm first: cp onto an existing symlink writes through it and clobbers the
  # file it points at.
  rm -f "$BIN_DIR/$t"
  if [ "$LINK" = 1 ]; then ln -s "$SRC_DIR/$t" "$BIN_DIR/$t"; else cp "$SRC_DIR/$t" "$BIN_DIR/$t"; fi
  echo "installed $BIN_DIR/$t"
done

command -v jq >/dev/null || echo "warning: jq not found; the tools need it (brew install jq)"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) cat <<EOF

note: $BIN_DIR is not on your PATH. Add this line to ~/.zprofile, then open a new terminal:
  export PATH="$BIN_DIR:\$PATH"
EOF
  ;;
esac

case " ${TOOLS[*]} " in *" claude-sessions "*)
  [ -d /Applications/iTerm.app ] || [ -d "$HOME/Applications/iTerm.app" ] ||
    echo "warning: iTerm2 not found; claude-sessions restore reopens sessions in it"
  # Absolute path, so the hooks work whatever PATH Claude Code was started with.
  cmd="$BIN_DIR/claude-sessions save --from-hook"
  cat <<EOF

To snapshot sessions automatically, add these hooks to ~/.claude/settings.json
(merge them into its "hooks" object if it already has one):

  "hooks": {
    "SessionStart": [{"matcher": "", "hooks": [{"type": "command", "command": "$cmd", "timeout": 10}]}],
    "SessionEnd":   [{"matcher": "", "hooks": [{"type": "command", "command": "$cmd", "timeout": 10}]}]
  }
EOF
  ;;
esac
