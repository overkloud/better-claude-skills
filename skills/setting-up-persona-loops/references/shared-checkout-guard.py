#!/usr/bin/env python3
"""Claude Code PreToolUse hook (matcher: Bash) for a checkout shared by
several persona sessions.

Several loop sessions edit one working tree. The only thing that keeps their
uncommitted work apart is that every commit names its paths. One broad add
(`git add -A`, `git commit -a`) sweeps a neighbour's half-written files into a
commit with an unrelated message, and the neighbour cannot even see it
happened — its files simply go clean. This hook refuses the git commands that
touch files a session did not name:

  git add -A / --all / -u / .          stage everything
  git add <directory>                   stage everything dirty under it
                                        (the 2026-09-16 sweep was `-A docs/`)
  git commit -a / -am / --all           commit everything
  git stash (push/pop/apply/drop/clear) the stash stack is shared too
  git pull --rebase / --autostash       refuses on any dirty file, or pockets a
                                        neighbour's work; sync with
                                        `git fetch && git merge --ff-only`
  git reset --hard, git clean,          discard a neighbour's uncommitted work
  git checkout|restore .

Wire it in the repo's `.claude/settings.json` (tracked, so every session and
worktree gets it):

  {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
      {"type": "command", "command": "python3 bin/shared-checkout-guard"}]}]}}

Self-test: `python3 bin/shared-checkout-guard --test`.
"""

from __future__ import annotations  # macOS ships python3 3.8: no runtime generics

import json
import os
import re
import shlex
import sys
import tempfile

# One (pattern, reason) per forbidden shape. `git` may carry global options
# (`-C <dir>`, `-c k=v`) between the word `git` and the subcommand.
_GIT = r"\bgit\s+(?:(?:-C\s+\S+|-c\s+\S+|--no-pager)\s+)*"
_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(_GIT + r"add\b(?=(?:\s+\S+)*\s+(?:-A|--all|-u|--update|\.|:/\.?)(?:\s|$))"),
        "`git add` without explicit paths stages a neighbour session's uncommitted "
        "work. Name every file: `git add -- <path> <path>`.",
    ),
    (
        re.compile(_GIT + r"commit\b(?=(?:\s+\S+)*\s+(?:--all|-[a-zA-Z]*a[a-zA-Z]*)(?:\s|$))"),
        "`git commit -a` commits every dirty file, including a neighbour session's. "
        "Commit named paths only: `git commit -m '...' -- <path> <path>`.",
    ),
    (
        re.compile(_GIT + r"stash\b(?!\s+(?:list|show)\b)"),
        "The stash stack is shared across sessions and worktrees: `git stash` pockets "
        "(or re-applies) a neighbour's work. Leave dirty files alone.",
    ),
    (
        re.compile(_GIT + r"pull\b(?=(?:\s+\S+)*\s+(?:--rebase|-r|--autostash)(?:\s|$|=))"),
        "`git pull --rebase` refuses whenever any file is dirty (a neighbour's included) "
        "and `--autostash` pockets their work. Sync with "
        "`git fetch -q origin && git merge --ff-only origin/main`.",
    ),
    (
        re.compile(_GIT + r"reset\b(?=(?:\s+\S+)*\s+--hard(?:\s|$))"),
        "`git reset --hard` discards a neighbour session's uncommitted work.",
    ),
    (
        re.compile(_GIT + r"clean\b"),
        "`git clean` deletes a neighbour session's untracked filings (an uncommitted "
        "task file is a filing, not litter).",
    ),
    (
        re.compile(_GIT + r"(?:checkout|restore)\b(?=(?:\s+\S+)*\s+(?:\.|:/\.?)(?:\s|$))"),
        "`git checkout .` / `git restore .` discards every session's uncommitted work. "
        "Restore named paths only.",
    ),
]


_GIT_ADD_SEGMENT = re.compile(_GIT + r"add\b(?P<args>[^|;&\n]*)")

_DIR_REASON = (
    "`git add <directory>` stages everything dirty under it, a neighbour session's "
    "files included (the 2026-09-16 sweep was `git add -A docs/`). Name every file: "
    "`git add -- <path> <path>`."
)


def _adds_a_directory(command: str, cwd: str) -> bool:
    """True when any `git add` pathspec in the command is an existing directory."""
    for match in _GIT_ADD_SEGMENT.finditer(command):
        try:
            args = shlex.split(match.group("args"))
        except ValueError:
            continue
        for arg in args:
            if arg.startswith("-") and arg != "--":
                continue
            if arg != "--" and os.path.isdir(os.path.join(cwd, arg)):
                return True
    return False


_HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?\n\1(?:\n|$)", re.DOTALL)


def violation(command: str, cwd: str = ".") -> str | None:
    """Return the reason the command is refused, or None."""
    # Only the shell words matter: drop heredoc bodies (commit messages),
    # backtick spans and quoted strings so prose mentioning `git add -A` passes.
    stripped = _HEREDOC.sub("\n", command)
    stripped = re.sub(r"`[^`]*`", "''", stripped)
    stripped = re.sub(r"'[^']*'|\"[^\"]*\"", "''", stripped)
    for pattern, reason in _RULES:
        if pattern.search(stripped):
            return reason
    if _adds_a_directory(stripped, cwd):
        return _DIR_REASON
    return None


def _self_test() -> int:
    denied = [
        "git add -A",
        "git add --all && git commit -m x",
        "git add .",
        "git add -u",
        "git -C /repo add -A",
        "git commit -a -m 'x'",
        "git commit -am 'x'",
        "git commit -qam 'x'",
        "git commit --all -m x",
        "git stash",
        "git stash push",
        "git stash pop",
        "git pull --rebase",
        "git pull --autostash origin main",
        "git reset --hard HEAD~1",
        "git clean -fd",
        "git checkout -- .",
        "git restore .",
        "cd docs && git add . && git commit -m 'sweep'",
    ]
    allowed = [
        "git add -- docs/a.md docs/b.md",
        "git add docs/a.md",
        "git add -p docs/a.md",
        "git commit -m 'x' -- docs/a.md",
        "git commit -s -m 'x' -- docs/a.md",
        "git commit --amend --no-edit",
        "git commit -m 'note: never git add -A here' -- docs/a.md",
        "git commit -F - -- docs/a.md <<'EOF'\nfix: the engineer's `git add -A docs/` swept it\n\n"
        "never git stash or reset --hard in docs/\nEOF\ngit log -1",
        "git add -- docs/a.md && git commit -F - -- docs/a.md <<EOF\n"
        "refuses `git add <directory>` too\nEOF",
        "git stash list",
        "git fetch -q origin && git merge --ff-only origin/main",
        "git pull --ff-only",
        "git reset HEAD -- docs/a.md",
        "git reset --soft HEAD~1",
        "git checkout main",
        "git checkout -- docs/a.md",
        "git restore --staged docs/a.md",
        "git status --short",
        "git log --oneline -5",
        "git diff -- .",
    ]
    # Directory pathspecs need a real tree: `docs/` exists, `docs/a.md` is a file.
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmp, "docs", "sub"))
    open(os.path.join(tmp, "docs", "a.md"), "w").close()
    denied += ["git add docs/", "git add -A docs/", "git add docs/sub", "git add -- docs"]
    allowed += ["git add docs/a.md", "git add -- docs/a.md docs/missing.md"]
    failures = 0
    for cmd in denied:
        if violation(cmd, tmp) is None:
            print(f"FAIL should deny : {cmd}")
            failures += 1
    for cmd in allowed:
        reason = violation(cmd, tmp)
        if reason is not None:
            print(f"FAIL should allow: {cmd}\n      ({reason})")
            failures += 1
    print(f"{len(denied)} denied, {len(allowed)} allowed, {failures} failures")
    return 1 if failures else 0


def main() -> int:
    if "--test" in sys.argv[1:]:
        return _self_test()
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    if payload.get("tool_name") != "Bash":
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    reason = violation(command, payload.get("cwd") or os.getcwd())
    if reason is None:
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        "[shared-checkout-guard] " + reason
                        + " Several persona sessions share this working tree; "
                        "only pathspec-limited git commands are allowed."
                    ),
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
