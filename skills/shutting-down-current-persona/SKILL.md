---
name: shutting-down-current-persona
description: Use when standing down the persona armed in the current Claude Code session so the session can be closed safely — ending its /loop, closing or parking claimed work items, recording what must be re-armed, and writing the handover into the prompt file. Triggers on "shut down this persona", "I want to close this session", "stop the loop and hand over", a session running out of context, or a persona being re-armed elsewhere.
---

# Shutting Down the Current Persona

## Overview

A persona is armed by pasting a role-scoped prompt into a fresh session; the session
then self-paces with `/loop`. Standing it down is the inverse: **get everything back
onto disk and into git, then stop.** The session's chat context is the only thing
allowed to die.

Survives a shutdown: the prompt file (with a fresh `CURRENT STATE` block), the bus,
the journal, the comm ack, committed branches and recorded worktrees. Does not
survive: the loop, Monitor tasks, crons, and everything this session knew but never
wrote down.

This skill stands down **the persona armed in the session running it** — one session,
one role. It does not retire the persona: pasting the prompt into a fresh session
re-arms it. Setting a loop up is `setting-up-persona-loops`.

## When to Use

- The user wants to close this session — machine going down, done for the day, or
  the session is being moved to another checkout or model tier.
- Context is nearly exhausted and the clean move is a handover to a successor session
  rather than dying mid-item. A compaction notice is the signal to start: the
  stand-down itself spends tokens on reading, parking, and the verification step.
- A session is wedged and will be replaced.

Not for: retiring a persona permanently (a `to-user` proposal, then a removal — see
`setting-up-persona-loops`), or a momentary pause (just let the loop wake).

## The Rule

**A stood-down session must be indistinguishable from one that never ran, except for
what it wrote down.** Every claimed item is closed or parked, every session-only thing
is recorded with the exact invocation that re-arms it, every commit is pushed, and
`CURRENT STATE` answers what the successor's first wake will ask.

Shutdown is a *stop*, not a sprint. It starts no work, deploys nothing, and decides
nothing an open item left open.

## Sequence

Work the checklist in `references/shutdown-checklist.md` — it carries the exact
commands and the three templates (parked-item note, `CURRENT STATE` block, journal
entry). Order matters; the first step is what makes the rest safe.

1. **Stop the clock, then freeze intake.** End the loop by the mechanism that started
   it, delete this session's cron and any Monitor task it armed, and **copy each exact
   invocation into RE-ARM before deleting it**. **Leave your heartbeat file where it
   is** — an absent heartbeat means "never looped", the worst state in the liveness
   taxonomy, and deleting it makes a clean stand-down look like the failure the pod
   watches hardest for. From here on claim nothing new: a wake that fires mid-drain
   re-claims an item and undoes the work you just did.
2. **Take stock in one pass.** Sync fast-forward-only (`git fetch -q origin && git
   merge --ff-only origin/main` — never `pull --rebase` in a shared checkout), read
   the comm (the `shutdown` order may already be there, and a neighbour may have
   posted something you must answer before going), then list: items addressed to your
   role with `status: in-progress`, live worktrees and branches, uncommitted work of
   your own, unpushed commits, open soaks with their T0, active incidents.
3. **Finish only what is near-done** (definition below). One pass. Anything that does
   not close in it gets parked.
4. **Park the rest.** `status: todo` plus a dated note saying exactly where the work
   got to, what was verified, the branch and sha, and what comes next. Commit it.
   Never leave an item `in-progress`: a successor cannot tell that apart from a session
   that died, and at 24 h it is filed as an `ops-issue`.
5. **Leave the workspace resumable.** Every live worktree is either removed (its work
   merged and verified) or recorded — path, branch, last commit, whether tests were
   green. Uncommitted work in a worktree gets a wip commit on its branch or the
   successor loses it. Never delete a worktree holding unmerged work.
6. **Write the handover into the prompt file.** A new `## CURRENT STATE (<date time
   TZ>)` block on top, the previous one moved under `## Previous state`. Chat does not
   survive this session; the prompt file is the only channel to the successor. Carry
   what it cannot reconstruct from git, the bus and the journal — deployed sha, open
   soak and its T0, where each parked item got to, the first check to run — each
   stated exactly enough to act on. Pay the prompt debt here too: any rule this
   session learned goes in dated, with its cause.
7. **Journal the stand-down** — append-only, your own section in the day-file: when you
   stood down, why, what was left open.
8. **Commit, push, and tell the pod.** Commit **named paths only** (`git commit -m …
   -- <file> <file>`; a directory pathspec sweeps a neighbour's in-flight work) and
   push — an unpushed commit is invisible to every other session. Then post
   `ack: <role> stood down at <HH:MM>` to the comm: that entry is what stops a live
   neighbour from reading your freezing heartbeat as a crash. <Operator:> you go last
   — collect the others' acks first, file what nobody could close, then post
   `note: pod down`.
9. **Name the gap out loud.** Say which env is unmonitored from what time, what no
   longer self-heals, and what the user should watch. For a user-facing or prod env,
   file a `to-user` `ops-issue` as well. Whether to accept the gap or hand it to
   another live session is the user's call, not yours.
10. **Verify, then declare.** Run the verification commands and show their output: no
    `in-progress` items addressed to your role, clean `git status` in your pathspecs,
    empty `git log origin/<branch>..HEAD`, `git worktree list` matching `CURRENT
    STATE`. Only then tell the user it is safe to close. Evidence before the claim.

## What "near-done" means

An item is near-done only when **the work is already verified and what remains is
bookkeeping**: merge a branch that already passed its whole-branch review, write the
`## Outcome`, `git mv` to `done/`, file the follow-up item to the next role.

It is *not* near-done — park it — if closing it would need any of: writing or
continuing implementation, running a review, a deploy, restart, promotion or any other
env action, a soak, or a judgment the item itself does not already settle. Ambiguity
fails closed here exactly as it does in the loop: park with the question, never guess
to tidy up.

The ceiling is one pass and no new implementation subagents (a verification run is
fine). A shutdown that starts shipping is how a session that was five minutes from
closing spends an hour and dies mid-merge anyway.

## Quick Reference

| Thing | Must end up | Never |
|---|---|---|
| Item you claimed | `done/` with an Outcome, or `todo` with a dated parked note | left `in-progress` |
| Loop, Monitor, cron | stopped/deleted, exact invocation copied into RE-ARM | stopped silently, or left running against a dead session |
| Worktree with unmerged work | recorded in CURRENT STATE (path, branch, last commit, test state) | deleted, or left with uncommitted changes |
| What you learned today | a dated rule in the prompt file | in the chat transcript |
| Deployed sha, open soak, incident | the new CURRENT STATE block | in your head |
| The handover's content | what the successor cannot reconstruct from git, the bus and the journal, stated exactly | a narrative of the session's day |
| Any commit | pushed, named paths only | `git add -A`, a directory pathspec, `commit -a` |
| Your heartbeat file | left in place to go stale, explained by your comm ack | deleted — that reads as "never looped" |
| The fact that you stopped | an `ack: <role> stood down` in the comm | silence, and a neighbour filing you as `down` |
| An env losing its monitor | said out loud, plus a `to-user` ops-issue if user-facing | assumed the user knows |
| "Safe to close" | after the verification commands, quoting their output | as the first sentence |

## Common Mistakes

- **Draining before stopping the loop** — the next wake fires mid-shutdown, claims a
  fresh item, and the session you just tidied is dirty again. Stop the clock first.
- **Recording state in the final chat message** — the successor never sees chat. If it
  is not in the prompt file, the bus, or the journal, it does not exist.
- **Leaving an item `in-progress` "because it's nearly done"** — nearly done and parked
  is a handover; nearly done and claimed is a mystery that gets flagged as a dead
  session.
- **Committing without pushing** — invisible to every other persona, and lost with the
  machine.
- **Disarming a Monitor without saving its invocation** — the successor rebuilds it
  from prose and reintroduces the false alerts the checked-in script exists to prevent.
- **"Finishing" something that needed a decision** — a shutdown is the worst moment to
  choose an interpretation. Park it with the question.
- **Deleting a worktree to leave things clean** — clean is not the goal; resumable is.
  Unmerged work is deleted only by the session that decides to abandon it.
- **A handover that retells the day** — the successor reads this block on a fresh
  window and pays for every line. Each one is a fact it cannot re-derive from git,
  the bus or the journal; the exact sha, value or command it must act on stays
  spelled out in full.
- **A CURRENT STATE block with no timezone, or appended at the bottom** — blocks are
  newest-first and dated with a TZ; a successor that tails the file misses same-day
  entries.
- **Silent about the gap** — the loop's whole value is that something is watching. The
  moment it stops, say so, with the time.
- **Deleting the heartbeat to tidy up** — absent and stale are different failures and
  the pod treats absent as the worse one, reported at once with no second test. A
  stood-down session leaves a stale heartbeat and an ack; it never leaves a hole.
- **Syncing with `pull --rebase`** — in a shared checkout it refuses on any dirty
  file, which is the normal state, so the sync silently does not happen and you stand
  down against a stale tree. `fetch` + `merge --ff-only`.
- **Declaring "safe to close" unverified** — the one claim in this whole procedure the
  user acts on directly. Quote the commands and their output.
