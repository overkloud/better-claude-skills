# better-claude-skills

A collection of Claude Code skills and settings.

## Skills

| Skill | Purpose |
|-------|---------|
| [`setting-up-persona-loops`](skills/setting-up-persona-loops/SKILL.md) | Set up autonomous, long-running Claude Code role sessions ("personas") that coordinate through git-tracked work items with no human nearby. |
| [`shutting-down-current-persona`](skills/shutting-down-current-persona/SKILL.md) | Stand down the persona armed in the current session — stop the loop, close or park claimed work, write the handover — so the session can be closed safely. |
| [`shutting-down-all-personas`](skills/shutting-down-all-personas/SKILL.md) | Stand down a whole pod: one `shutdown` entry in the shared comm that every live persona acts on at its next wake, then verify the acks. |

## Install a skill

Copy or symlink a skill directory into `~/.claude/skills/`:

```sh
ln -s "$(pwd)/skills/setting-up-persona-loops" ~/.claude/skills/setting-up-persona-loops
```

## Contributing

No personal data, credentials, hostnames, or project-specific identifiers go in this repo. Keep skills generic.
