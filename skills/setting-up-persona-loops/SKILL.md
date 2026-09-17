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

## The Design, in Nine Rules

1. **Roles by permission, not by topic.** Implementers never operate an environment
   (no deploys, restarts, env edits, DB writes); operators never change application
   code — they investigate, self-heal per runbook, then *file* code work. Prod
   operators execute approved items only; rollback is always allowed. Researchers
   touch nothing.
2. **All state is durable.** A dead session loses nothing; re-arm by pasting the prompt.
   Session-only state (crons, Monitor tasks) gets an explicit **RE-ARM** section, and a
   fresh session reconciles recorded state against reality before acting.
3. **One session per role ⇒ zero locking — but one checkout ⇒ three git rules.** The
   bus needs no locks because only the addressed role changes `status` and only the
   author edits the body. Sessions that share a working tree keep their uncommitted
   work apart by nothing but discipline, so every prompt carries, and a hook enforces:
   sync with `git fetch -q origin && git merge --ff-only origin/main` (never
   `pull --rebase`, which refuses on any dirty file, nor `--autostash`, which pockets
   a neighbour's work); commit **named paths only** (`git commit -- <paths>`, never
   `add -A` / `commit -a`); never stash, reset, clean or restore what you did not
   write. Bus/journal edits commit immediately (`journal:` prefix). A breach is
   reported as a dated Traps entry in the offender's prompt by whoever caught it,
   not to the user (`references/persona-prompt-template.md` → "Shared checkout").
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
9. **The pod is a required pair plus options, and it talks through a transient
   channel.** The live sessions of one app form a *pod*. Two personas are
   **required** — the operator and the engineer — and each watches the other's
   heartbeat; every other role is optional and its queue waits while it is down.
   The operator also owns **non-technical** work (docs, guides, bookkeeping, process,
   data fixes through the API): a task's `Owner:` line routes it. Pod members talk
   between wakes through a **shared comm**: one day-file, append-only, read every
   wake, pruned by the operator after 7 days. A guide change is announced there as a
   `guide-update`, and the named persona **re-arms** — re-reads its guide from disk
   and re-runs its liveness section — in that wake. Nothing of record lives in the
   comm (`references/comm-readme-template.md`).

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
   is the task backlog (see archetypes → "No-bus variant"). Create the **shared comm**
   either way: `docs/operation/<app>/comm/README.md` from
   `references/comm-readme-template.md`; day-files appear on first use.
4. **Write one resume prompt per role** at `docs/operation/<app>/<role>-loop-prompt.md`
   from `references/persona-prompt-template.md`, plus `docs/operation/<app>/README.md`
   (persona table). Personas of different apps are **mutually out of scope** — say so in
   every prompt.
5. **Make the dangerous boundaries structural**, not prose: a permission hook that
   denies prod-file edits, a checked-in monitor script (never rebuilt from prose each
   session), read-only DB wrappers for non-operators, and — whenever two sessions
   share a working tree — `references/shared-checkout-guard.py` copied to `bin/` and
   wired as a **tracked** PreToolUse hook in `.claude/settings.json` (its docstring
   has the snippet; `--test` is the smoke test). It refuses `git add -A`, `git add`
   of a directory, `commit -a`, `stash`, `pull --rebase`, `reset --hard`, `clean` and
   `checkout .`. The prose rule alone was broken within a day of a third session
   joining a tree (2026-09-16: an engineer commit's `git add -A docs/` swept the
   operator's half-written ledger — a directory pathspec is not "named paths").
6. **Register**: docs index, project instructions' docs table, scheduled-jobs registry
   (a persona that watches a job is named on the job's row).
7. **Smoke-test the protocol**: walk one synthetic item `next/` → claim → `done/` with
   an `## Outcome`, read back by the receiving role.
8. **Arm the required pair first** (operator, then engineer), then the optional
   roles: paste each prompt into its own fresh session, set the session model to
   the persona's recommended tier (`/model`), then `/loop <interval>`
   (operators ~900 s, engineer/research ~1800 s, product manager ~3600 s). From
   then on a guide edit is a `guide-update` in the comm and the persona re-arms
   itself; a dead session is the only thing that needs a human paste again.
9. **Verify each arming actually took** — `/loop` is a separate step from
   pasting the prompt, and a persona that got the paste but not the loop looks
   *fine*: it answers, it works, it commits. It simply never wakes again.
   Per persona, before moving on: `CronList` is non-empty in that session, and
   `~/.<app>/<role>-heartbeat` **exists** on disk. Then confirm the pair sees
   each other — each required persona's first wake should read its neighbour's
   heartbeat and find it. A `~/.<app>/` holding heartbeats for some roles and
   not others is the signature of this failure, and it is worth an explicit
   `ls ~/.<app>/` at the end of setup.
10. **Know how to stand down.** Closing a window is not a shutdown: an item left
    `in-progress` and a heartbeat that just stops are indistinguishable from a crash.
    One session stands down through the `shutting-down-current-persona` skill; the
    whole pod through `shutting-down-all-personas`, which posts one `shutdown` entry
    to the comm that each persona acts on at its next wake.

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
| Non-technical change (docs, a guide, index bookkeeping, process, a data fix through the API) | operator, via a task with `Owner: operator` | engineer spending a cycle on it |
| Something a neighbour needs *this wake* (a guide changed, a required persona is down, a breach) | shared comm day-file | a task file, a prompt edit, or the user |
| Anything that must outlive a week | guide (rule), ledger (fact), task file (work) | the comm |
| Closing one persona session | stand-down: stop loop + cron, park claims, CURRENT STATE, `ack` to the comm | closing the window on an `in-progress` item |
| Closing the whole pod | a `shutdown` entry addressed to `pod`; each persona stands itself down at its next wake | killing sessions, or standing the operator down before it has collected the acks |

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
- **Broad add in a shared checkout** — `git add -A` / `commit -a` sweeps a
  neighbour's half-written files into a commit with an unrelated message, and the
  neighbour cannot see it happen: its files simply go clean. The guard hook refuses
  it; once it has happened, the content is on `main` under the wrong message — do
  not rewrite a shared commit, record where the content landed, and append a dated
  trap to the offender's prompt.
- **Breach reported to the user** — a cross-persona protocol breach (a swept
  commit, an edited `in-progress` file, a skipped sync) is a dated entry in the
  offending persona's "Traps", written by whoever caught it. That prompt is the
  offender's memory and the channel that reaches its next wake (a `breach` comm
  entry points it there); a breach is not a remit change, so it needs no `to-user`
  proposal. The user hears of it only when it recurs.
- **Guide edited, nobody told** — a persona keeps running the rules it was armed
  with until it re-reads its guide. Every guide edit posts a `guide-update` to the
  comm (file + sha); the operator posts it on behalf of anyone who forgot, from
  `git log -- <guides>`.
- **Comm as a record** — a decision, a fact, or a rule written only in the comm is
  gone in 7 days. The comm is for what a neighbour needs this wake; durable
  content goes to the guide, the ledger, or a task file.
- **Optional persona treated as required** — the pod is live when the operator and
  the engineer are; a down product manager means its queue waits, not that the
  engineer absorbs feature-requests without a `## Need`.
- **Armed but not looping** — the prompt was pasted and `/loop` never was, so the
  session runs once and never wakes. Nothing inside it can notice: its own
  `CronList` backstop only runs on a tick, and it never ticks. Nothing outside
  it notices either unless `down` is defined over an **absent** heartbeat as
  well as a stale one — "older than N minutes and no commits since" cannot
  evaluate a file that does not exist, and a neighbour that meets one reports
  the state and moves on. Define absent as `down` at once (2026-09-16: an
  operator ran unlooped while its `~/.<app>/` neighbours both had crons; the
  engineer found the file missing and correctly refused to force it into a
  taxonomy that had no slot for it). Never write a dated grace clause for a
  missing heartbeat — "it only means that session predates this check" has no
  expiry and permanently disarms the one signal that catches this.
