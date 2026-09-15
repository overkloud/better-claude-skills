---
name: setting-up-persona-loops
description: Use when a repo needs autonomous, long-running Claude Code role sessions ("personas" — operator/monitor, engineer, product manager, researcher, prod operator, app operator) that coordinate through files in git with no human nearby, when adding a persona to an existing loop, or when a persona keeps overstepping its role or stalling on unclaimed work.
---

# Setting Up Persona Loops

## Overview

A **persona** is a role-scoped resume prompt checked into the repo. Pasting it into a
fresh Claude Code session arms that role; the session then self-paces with `/loop`.
Several personas form a closed loop by passing **role-addressed work items** through a
git-tracked bus directory. The human is a gate only for irreversible or costly actions.

Core principle: **split roles by who is *allowed* to do the work, keep every bit of
state on disk/DB/git so sessions are disposable, and make the prompt itself the
persona's memory.**

## When to Use

- Something runs 24/7 (a service, a data pipeline, scheduled jobs) and needs
  monitoring/self-heal, fixes, and analysis without a human present.
- Two duties keep colliding in one session: a responsive operator poll vs. hours of
  uninterrupted implementation → split them.
- Work items sit unclaimed, get done by the wrong role, or lose state when a session dies.

Not for: a one-off task, or a single short-lived session (just write a plan).

## The Design, in Eight Rules

1. **Roles by permission, not by topic.** Implementers never operate an environment
   (no deploys, restarts, env edits, DB writes); operators never change application
   code — they investigate, self-heal per runbook, then *file* code work. Prod
   operators execute approved items only; rollback is always allowed. Researchers
   touch nothing.
2. **All state is durable.** A dead session loses nothing; re-arm by pasting the prompt.
   Session-only state (crons, Monitor tasks) gets an explicit **RE-ARM** section, and a
   fresh session reconciles recorded state against reality before acting.
3. **One session per role ⇒ zero locking.** The bus needs no locks because only the
   addressed role changes `status` and only the author edits the body. Every cycle
   starts with `git pull --rebase`; bus/journal edits commit immediately (`journal:` prefix).
4. **Human gates only for the irreversible.** Everything else self-heals or proceeds.
   Cost-bearing ambiguity **fails closed**: reject and ask, never guess.
5. **Diagnoses are leads, not findings.** A handed-over cause is reproduced from primary
   evidence before it is fixed.
6. **Lessons go into the prompt.** Every incident that changed a rule appends a dated
   rule or a "Traps that have already bitten" entry. Prompts are living runbooks.
7. **Sessions orchestrate; subagents do the work.** A persona session is a long-lived
   loop whose context window is its lifespan. Every non-trivial task (an investigation
   over many files, an implementation, a review, a data scan, a UI walk) is dispatched
   to a subagent that returns a conclusion; the session keeps the verdict, not the
   file dumps. The model tier is chosen per task by complexity — small for mechanical
   lookups, medium (e.g. Sonnet) for general coding and per-task reviews, large for
   planning, whole-branch review, and root-cause work (table in
   `references/archetypes.md` → "Delegation and model tiers").
8. **Someone owns "less".** Every other role adds: findings, fixes, features, rules.
   The product-manager persona exists to subtract — features that do not serve the core
   value, UX steps that add friction, process that gates nothing. Feature-requests route
   through it; removals of shipped behavior are a user gate.

## Setup Recipe

1. **Choose roles and gates.** Pick from `references/archetypes.md`. Choose role tokens
   that are **prefix-safe** — none is a prefix of another — and short (`dev`/`eng`/`pdm`/`prod`,
   never `dev`/`developer`: `to-dev-` is a prefix of `to-developer-` and every glob
   would sweep both).
   Name the human gate(s) explicitly (e.g. prod promotion).
2. **Write the design spec** (`docs/impl/specs/<date>-<loop>-design.md`): goal, a
   decisions table (gates, cadence, protocol), a roles table (prompt file + remit),
   the bus layout, the promotion ladder, error handling (dead sessions, git conflicts).
3. **Create the bus**: `docs/<bus>/{PROTOCOL.md,next/,done/}` from
   `references/bus-protocol-template.md`. Skip the bus for a single persona — its queue
   is the task backlog (see archetypes → "No-bus variant").
4. **Write one resume prompt per role** at `docs/operation/<app>/<role>-loop-prompt.md`
   from `references/persona-prompt-template.md`, plus `docs/operation/<app>/README.md`
   (persona table). Personas of different apps are **mutually out of scope** — say so in
   every prompt.
5. **Make the dangerous boundaries structural**, not prose: a permission hook that
   denies prod-file edits, a checked-in monitor script (never rebuilt from prose each
   session), read-only DB wrappers for non-operators.
6. **Register**: docs index, project instructions' docs table, scheduled-jobs registry
   (a persona that watches a job is named on the job's row).
7. **Smoke-test the protocol**: walk one synthetic item `next/` → claim → `done/` with
   an `## Outcome`, read back by the receiving role.
8. **Arm**: paste each prompt into its own fresh session, set the session model to
   the persona's recommended tier (`/model`), then `/loop <interval>`
   (operators ~900 s, engineer/research ~1800 s, product manager ~3600 s).

## Quick Reference

| Need | Goes to | Never |
|---|---|---|
| Code change, test, migration file | engineer | operator implementing it inline |
| Env lever, deploy, restart, apply merged migration | the env's operator | engineer touching any env |
| Analysis of recorded data | researcher | researcher editing config |
| Prod change | user-approved item, executed by prod operator | prod operator self-approving |
| Item finished by one role, next step another's | close it; file a **new** item | one item spanning two roles |
| Feature-request (anything beyond a bug fix) | product manager: cut, shrink, or forward `to-eng` | engineer absorbing it as specified |
| Removing shipped behavior, a whole feature, a persona | `to-user` proposal from the product manager | product manager or engineer removing it directly |
| Non-trivial work inside any session | a subagent, model tier by complexity | the session doing it inline |

## Common Mistakes

- **Acting before claiming** — bus status must track reality; claim (`in-progress`,
  commit) first even when the work was triggered elsewhere.
- **Counting instead of reading** — "actionable" is decided by reading each item's
  status line every wake; a stable file count proves nothing. A named gate is a
  condition to re-probe, not a verdict.
- **Untracked filings** — an uncommitted item is invisible to the claim protocol; land it
  after one grace wake rather than leaving it alone forever.
- **Proxy health checks** — a predicate that is still true when the system is healthy is
  a proxy; alert on state transitions, and give recovery a dead band.
- **Overwriting a shared day-file** — journals are append-only; each role appends its own
  section.
- **"Merged" reported as "deployed"** — a soak request names the exact sha; verify on
  the target branch/env, and put the command + result in the Outcome.
- **Stale task files** — re-verify line references and "still broken" claims against
  the main branch before scoping.
- **Outcome = "done"** — outcomes carry numbers, verdicts, shas, links.
- **Session does the work itself** — "it's only a few files" is how a loop session
  fills its context by mid-day and dies with an item `in-progress`. Dispatch; keep
  the conclusion.
- **Feature absorbed as specified** — a request is a symptom of a need; the product
  manager names the need, then finds the smallest change (often a removal) that
  serves it. Adding is the default of every other role, so the check is structural,
  not a reminder.
- **Guessing through ambiguity** — an implementer that picks an interpretation
  silently ships the wrong thing with confidence. State assumptions in the plan;
  when readings diverge materially, park the item with the question.
