# Broadcast and verify — the pod stand-down

Replace `<app>`, `<roles>`, `<bus>`, `<todo dir>` from the pod's README
(`docs/operation/<app>/README.md`) and each guide's header. Comm path:
`docs/operation/<app>/comm/`.

---

## 1. Pulse — before anything is posted

```sh
ls -l  ~/.<app>/*-heartbeat            # who is armed at all; absent = never looped
date; cat ~/.<app>/*-heartbeat         # ages: fresh / stale
git fetch -q origin && git merge --ff-only origin/main
sed -n '1,200p' docs/operation/<app>/comm/$(date +%F).md   # today's traffic
grep -HE '^(to|status):' <bus>/next/*.md                   # open claims, by role
grep -HiE '^(\*\*)?(Status|Owner)' <todo dir>/<app>_*.md   # the no-bus queue
git worktree list                                          # unmerged work
```

Mid-flight work that outranks a shutdown — name each one to the user before posting:

- a deploy recorded as started with no verification in the journal
- an open soak (its T0 and criteria) that abandoning resets
- a merged migration not yet applied
- a worktree with unmerged commits
- a `to-user` item waiting on an answer

## 2. The order

One entry, addressed to `pod`, in today's comm file (create it with
`# Comm — YYYY-MM-DD` if it does not exist):

```markdown
## HH:MM user → pod · shutdown: stand down for <reason>, from now
Every live persona (<roles>): stand down at your next wake, ahead of your other work,
by your guide's "Shutdown" section (skill: shutting-down-current-persona) — park or
close your claims, write CURRENT STATE, journal, commit named paths, push, post
`ack: <role> stood down at HH:MM`, leave your heartbeat in place, then stop.
<operator> goes last: collect the acks, file what nobody could close, prune, post
`note: pod down`. Expect the last ack by <HH:MM = now + slowest cadence>.
```

Commit and push at once — an unpushed order reaches nobody:

```sh
git commit -m "comm: shutdown order to pod" -- docs/operation/<app>/comm/$(date +%F).md
git push
```

## 3. The wait

| Role | Cadence | Ack expected by |
|---|---|---|
| operator / prod | ~900 s | now + 15 min |
| engineer / research | ~1800 s | now + 30 min |
| product manager | ~3600 s | now + 60 min |

Poll rather than block. Between checks there is nothing to do — a persona mid-wake
finishes its stand-down without help. The fast path for an impatient user is per role:
open that window and run `shutting-down-current-persona` there.

## 4. Verify — per role

```sh
git fetch -q origin && git merge --ff-only origin/main
grep -n 'stood down' docs/operation/<app>/comm/$(date +%F).md   # the acks
ls -l ~/.<app>/*-heartbeat; date                                 # fresh / stale / absent
grep -l '^status: in-progress' <bus>/next/*.md                   # expect: no matches
grep -HiE '^(\*\*)?Status: *in-progress' <todo dir>/<app>_*.md   # expect: no matches
git status --porcelain                                           # expect: nothing left dirty
git log --oneline -5                                             # the stand-down commits
```

Each armed role ends in exactly one state: **acked**, **still-looping** (no ack,
heartbeat fresh — wait), **crashed** (no ack, heartbeat stale, no commits since), or
**never-looped** (heartbeat absent). Silence alone is not a state.

## 5. Leftovers — one ops-issue per orphaned claim

```markdown
---
from: user
to: user
type: ops-issue
status: todo
priority: P2
created: YYYY-MM-DD
---

# <item> left `in-progress` by <role> at pod stand-down

## What / why
Pod stood down <HH:MM TZ>; <role> never acked (<heartbeat state>). The item is claimed
and its session is gone. Last commit touching it: <sha> <date>. Worktree: <path on
branch @ sha, or none>. The claim was deliberately left in place — it is what a fresh
<role> session resumes.

## Acceptance criteria
1. A fresh <role> session is armed and resumes the item, or
2. The item is released to `todo` by that role with a dated note of where it got to.
```

Without a bus, the same fact goes in the ledger or the task file's Status line — and
the Status line of a task claimed by a dead session is changed only by that role.

## 6. Report to the user

```markdown
**Pod stand-down ordered <HH:MM TZ>. <N> of <M> personas stood down.**

| Role | State | Window |
|---|---|---|
| <operator> | stood down <HH:MM>, acked | safe to close |
| <engineer> | stood down <HH:MM>, acked | safe to close |
| <pdm> | no ack, heartbeat fresh — next wake <HH:MM> | wait, or run shutting-down-current-persona in it |
| <research> | heartbeat absent — never looped | nothing running; safe to close |

- Unmonitored from <HH:MM TZ>: <env> — <what no longer self-heals>; <env> — <…>
- Open soak abandoned: <item>, T0 <time> (restart the clock on re-arm)
- Left `in-progress`: <items> — filed as <ops-issue links>
- Comm: order + acks in `comm/<date>.md` (transient — deleted in 7 days; the durable
  record is each persona's CURRENT STATE block)

**To bring the pod back:** paste `<operator guide>` into a fresh session, `/model
<tier>`, `/loop 900s`; then the engineer the same way; then the optional roles. Verify
each arming took: `CronList` non-empty in that session, and `ls ~/.<app>/` shows a
heartbeat per role.
```

If any verification came back non-empty, say so plainly and name what is still open. A
pod reported as down while a session is still looping is worse than no report: the user
closes a window mid-item on the strength of it.
