---
name: shutting-down-all-personas
description: Use when the whole pod of live persona sessions for a repo has to stop — closing the loop for the night, freeing the machine, or re-arming everything after a guide overhaul. Posts one `shutdown` entry to the shared comm that every persona acts on at its next wake, then verifies the acks so the user knows which windows are safe to close. Triggers on "shut down all personas", "close the pod", "stop the loop", "I'm done for the day, shut everything down".
---

# Shutting Down All Personas

## Overview

The live persona sessions of one app form a **pod**: a required operator and engineer,
plus whatever optional roles are armed. They talk between wakes through the shared comm
(`docs/operation/<app>/comm/YYYY-MM-DD.md`, read every wake). That channel is how a pod
is stood down: **one `shutdown` entry addressed to `pod`**, which each persona acts on
at its next wake by running the `shutting-down-current-persona` procedure in its own
session and posting its ack.

This skill is the broadcaster and the verifier. It does not stop anyone else's session,
and it cannot: a session is only stood down from inside. What it produces is the order,
the wait, and a per-role verdict the user can act on — which windows are safe to close,
which need a hand, and what stopped being watched.

Run it from the user's own session or from any pod member. Setting the pod up is
`setting-up-persona-loops`; standing down the one session you are in is
`shutting-down-current-persona`.

## When to Use

- The user is closing the loop for the night, freeing the machine, or going on leave.
- Guides changed enough that every persona should be re-armed from a fresh paste.
- The repo is being moved, archived, or handed over.

Not for: one session (that is `shutting-down-current-persona`), a pod with no comm
(stand each session down individually, oldest cadence first), or retiring a persona
permanently (a `to-user` proposal, then a removal).

## The Rule

**Broadcast, then verify — never seize.** A shutdown order does not suspend edit
rights: another role's claimed item, worktree, cron and heartbeat stay untouched even
when its session never answers. A persona that cannot stand itself down leaves work
that gets *filed*, not taken.

And the order is the user's to give. The pod exists because something needed watching;
the moment it stops, that thing is unwatched. This skill names what goes dark and gets
a yes before it posts anything.

## Sequence

Commands, templates and the report skeleton are in
`references/broadcast-and-verify.md`.

1. **Take the pod's pulse before ordering it down.** Who is actually live
   (`ls -l ~/.<app>/*-heartbeat` and their ages), and what is mid-flight: a deploy
   started but not verified, an open soak, an unapplied migration, an unmerged
   worktree, a `to-user` item waiting on an answer the user is about to walk away
   from. A pod ordered down mid-deploy leaves an env in a state nobody is watching.
2. **Say what goes dark, then get the go.** Which envs lose monitoring and self-heal,
   from when, what an open soak loses by being abandoned, and anything irreversible
   still in flight. The user decides; this skill never decides that the loop should
   stop.
3. **Post one `shutdown` entry addressed to `pod`.** Name the roles, the time, and the
   procedure each is to follow, so nobody improvises a shutdown of their own design.
   Six lines is the whole order — every live persona spends its window reading it, and
   the steps live in their own guides (`*-loop-prompt.md` → "Shutdown").
   Commit it `comm:`-prefixed with named paths and push immediately — an unpushed
   order reaches nobody.
4. **Touch nothing else.** No deleting another session's cron, no editing its claimed
   items, no removing its worktree, no `/loop` stop from outside. The entry is the
   whole mechanism.
5. **Wait by cadence, not by clock.** Each persona acts at its *next wake*, and the
   interval to use is the one **its own heartbeat publishes** — a quiet pod is exactly
   the state where personas have backed off, so a base-rate estimate runs short. Expect
   the last ack about one published interval after the post, up to the cap, and say so
   up front — a pod that looks unresponsive for two hours is usually just a backed-off
   persona between wakes.
   If the user will not wait, the fast path per role is to open that window and run
   `shutting-down-current-persona` in it.
6. **Go last if you are the operator.** The operator is the comm's custodian: it
   collects the acks, files what nobody could close, prunes, and posts `note: pod down`
   before standing itself down. Any other pod member stands down at its own wake like
   everyone else. A caller that is not a pod member skips this step.
7. **Verify per role, not in aggregate.** Every armed role ends in exactly one state:
   acked, still-looping, crashed, or never-looped — the table below tells them apart
   from the ack and the heartbeat. "No new comm entries" is not a verdict.
8. **File the leftovers and report.** Every `in-progress` item with no owner left alive
   becomes a `to-user` `ops-issue` naming the item, the role, and where the work got
   to. Then the report: per role, safe-to-close or needs-a-hand; what is unmonitored
   from what time; and the exact pastes that bring the pod back.

## Reading the pod after the order

| What you see | What it means | What you do |
|---|---|---|
| `ack: <role> stood down` in the comm | stood down cleanly | tell the user that window is safe to close |
| No ack, heartbeat fresh | still looping; its wake has not come yet | wait one more interval before concluding anything |
| No ack, heartbeat stale, no commits since | crashed, or died mid-stand-down | do not seize its claims — file the ops-issue; the user closes the window |
| Heartbeat absent | never looped: it never read the comm, so the order never reached it | check the bus for anything it claimed while running by hand, file it, user closes the window |
| Ack posted, heartbeat now stale | normal and expected | nothing — a stood-down persona leaves a stale heartbeat on purpose |

## Quick Reference

| Need | Goes to | Never |
|---|---|---|
| Stop every live persona | one `shutdown` entry addressed to `pod` | one entry per role, or a message in each window |
| Stop one session | `shutting-down-current-persona`, inside that session | an order from outside |
| A persona that never answers | a `to-user` ops-issue naming its open claims | taking its item, worktree or cron |
| The order's deadline | the slowest cadence in the pod, stated when posting | a clock time the personas cannot see |
| The last one out | the operator: acks collected, leftovers filed, `note: pod down` | the operator first, leaving the comm unpruned and the acks uncollected |
| Bringing the pod back | paste each guide into a fresh session, `/model`, `/loop` — required pair first | expecting a stood-down session to resume itself |

## Common Mistakes

- **Ordering the pod down mid-deploy** — the one moment an env most needs someone
  watching is the moment after a deploy nobody verified. Take the pulse first.
- **Posting per-role entries** — they drift: one says the procedure, the next says
  "stand down", a third gets edited. The comm is read by everyone; one entry addressed
  to `pod` is the whole order.
- **Seizing a silent persona's work** — a shutdown order does not transfer edit
  rights. The claim is what a fresh session resumes; take it and the resumption breaks.
- **Declaring the pod down from silence** — silence is the same shape as a persona
  between wakes. A verdict needs an ack or a heartbeat, per role.
- **Killing the windows to be quick** — a closed window is a crash: an item stays
  `in-progress`, the CURRENT STATE block is a day stale, and the next arming starts by
  reconciling a mess. The broadcast costs one wake.
- **Standing the operator down first** — it is the custodian; going first leaves the
  acks uncollected, the leftovers unfiled and the comm unpruned.
- **Forgetting the comm is transient** — the shutdown entry and every ack are gone in
  7 days. What must survive goes into each persona's `CURRENT STATE` (its own
  stand-down writes it) and into the ops-issues filed for the stragglers.
- **Silence about what stopped being watched** — the report names each env, the time
  it went dark, and what no longer self-heals. That is the whole reason the pod ran.
