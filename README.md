# better-claude-skills

A collection of Claude Code skills and settings.

## Skills

| Skill | Purpose |
|-------|---------|
| [`setting-up-persona-loops`](skills/setting-up-persona-loops/SKILL.md) | Set up autonomous, long-running Claude Code role sessions ("personas") that coordinate through git-tracked work items with no human nearby. |

## Install a skill

Copy or symlink a skill directory into `~/.claude/skills/`:

```sh
ln -s "$(pwd)/skills/setting-up-persona-loops" ~/.claude/skills/setting-up-persona-loops
```

## Contributing

No personal data, credentials, hostnames, or project-specific identifiers go in this repo. Keep skills generic.
