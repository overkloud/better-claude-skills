# Stand-down checklist

Create one todo per numbered item and work them in order. Replace `<role>`, `<bus>`,
`<journal>`, `<prompt>`, `<branch>` from the persona's own prompt header.

Nothing here starts work. If a step wants a decision, park the item and move on.

---

## 1. Stop the clock

- [ ] End the loop by the mechanism that started it (a self-paced `/loop` stops with a
      stop wakeup; an interval loop the user started, the user stops — ask them to).
- [ ] List this session's session-only tasks and **copy each exact invocation into the
      prompt's `## RE-ARM` section before deleting it**: crons, Monitor tasks, any
      background watcher. The invocation, not a description of it.
- [ ] Delete them (`CronList` → `CronDelete`), and clear the recorded cron id and
      the cadence/guide-sha state, so a successor does not inherit a dead session's
      backoff or believe it has already read the guide:
      `rm -f ~/.<app>/<role>-cron ~/.<app>/<role>-cadence ~/.<app>/<role>-guide-sha`.
- [ ] **Do not touch `~/.<app>/<role>-heartbeat`.** It goes stale on its own; absent
      would mean "never looped" and is reported by a neighbour at once.
- [ ] From this point: claim nothing new from the bus.

## 2. Take stock (one pass)

```sh
git fetch -q origin && git merge --ff-only origin/main   # never pull --rebase here

# The comm — the shutdown order, and anything a neighbour needs answered first
sed -n '1,200p' docs/operation/<app>/comm/$(date +%F).md

# Items you claimed — READ the status lines, never count files
grep -rlE '^to: <role>$' <bus>/next/   # then read status/priority from the matches

# Workspace
git status --porcelain                       # yours vs. a neighbour's dirty files
git log --oneline origin/<branch>..HEAD      # unpushed
git worktree list
```

Write down, for the handover: `in-progress` items, live worktrees and branches, open
soaks and their T0, the deployed sha, active incidents.

## 3. Finish only what is near-done

Near-done = already verified, only bookkeeping left (merge a reviewed branch, write the
`## Outcome`, `git mv` to `done/`, file the follow-up item).

Park instead if closing it needs: implementation, a review, a deploy/restart/promotion,
a soak, or any judgment the item does not already settle. One pass, no new
implementation subagents.

## 4. Park everything still claimed

Set `status: todo` and append, in the body:

```markdown
## Parked <YYYY-MM-DD HH:MM TZ> — session stand-down

- Got to: <what is actually done and verified, with the evidence>
- Branch/worktree: <branch> at <sha> (<tests green? / not run>)
- Next step: <the exact next action for whoever resumes>
- Open question: <only if one is blocking; otherwise omit>
```

Commit it (`journal:` prefix, pathspec-limited) before moving on.

## 5. Make the workspace resumable

- [ ] Each live worktree: uncommitted work gets a wip commit on its branch.
- [ ] Worktrees whose work merged and verified: `git worktree remove … && git branch -d …`.
- [ ] Every remaining worktree is named in `CURRENT STATE` with path, branch, last
      commit, and test state. Unmerged work is never deleted at shutdown.

## 6. Write the handover into `<prompt>`

Move the existing `## CURRENT STATE …` heading under `## Previous state (<date> —
historical)` and insert on top:

```markdown
## CURRENT STATE (<YYYY-MM-DD HH:MM TZ> — read this first)

**Session stood down <HH:MM TZ>.** Nothing is armed until you re-arm it (RE-ARM above).

- Re-arm on start: <cron / Monitor names — invocations are in RE-ARM>
- Deployed sha: <sha> on <env>; open soak: <item> T0 <time>, criteria <…>
- Parked items: <file> — <one line each: where it got to, next step>
- Live worktrees: <path> on <branch> @ <sha>, tests <green|not run>
- Active incidents: <none | …>
- Unmonitored since <HH:MM TZ>: <env> — <what no longer self-heals>
- First thing to verify: <the one check whose answer changes what you do next>
```

One line per bullet, each a fact the successor cannot re-derive from git, the bus or
the journal — and the sha, value or command it must act on written out exactly.

Then append any rule this session learned, dated with its one-line cause — and, if an
incident bit, a `## Traps that have already bitten` entry.

## 7. Journal

Append your own section to `<journal>/<date>.md` (never overwrite the day-file):

```markdown
# <date> (<role>)

## Stand-down <HH:MM TZ>
Reason: <user closing the session | context exhausted | re-arming elsewhere>.
Closed: <items>. Parked: <items>. Left running: <deploys, soaks>.
Unmonitored from now: <env, or none>.
```

## 8. Commit, push, and tell the pod

Named paths only — a directory pathspec sweeps a neighbour's in-flight work, and the
guard hook refuses it:

```sh
git commit -m "journal: <role> stand-down <date>" \
  -- <bus>/done/<item>.md <journal>/<date>.md <prompt>
git push            # or: say explicitly that no remote is configured
```

Then append your ack to today's comm file and commit it (`comm:` prefix):

```markdown
## HH:MM <role> → pod · ack: <role> stood down at HH:MM
Loop and cron stopped; heartbeat left to go stale on purpose. Parked: <items>.
Unmonitored from now: <env, or none>. Re-arm: paste `<prompt>`, `/loop <interval>s`.
```

<Operator only:> go last. Collect the other acks, file what nobody could close, prune
day-files older than 7 days, then post `note: pod down`.

## 9. Name the gap

Tell the user, in the final message: which env is unmonitored and from what time, what
no longer self-heals, what to watch. For a user-facing or prod env also file:

```markdown
---
from: <role>
to: user
type: ops-issue
status: todo
priority: P2
created: <date>
---

# <env> unmonitored from <HH:MM TZ> — <role> session stood down

## What / why
<What the monitor covered, what now goes unnoticed, expected blast radius.>

## Acceptance criteria
1. Persona re-armed (prompt pasted, model set, loop started), or
2. User accepts the gap with an end date.
```

## 10. Verify, then declare

```sh
grep -rlE '^to: <role>$' <bus>/next/ | xargs grep -l '^status: in-progress'  # expect: none
git status --porcelain                                        # expect: nothing of yours
git log --oneline origin/<branch>..HEAD                       # expect: empty
git worktree list                                             # expect: matches CURRENT STATE
ls ~/.<app>/<role>-heartbeat                                  # expect: still there
```

Then, and only then, the final report — quoting what you just ran:

```markdown
**<role> persona stood down at <HH:MM TZ>. Safe to close this session.**

- Loop: stopped. Re-arm needs: <cron/Monitor names> (invocations in the prompt's RE-ARM)
- Items: <N> closed (<links>), <N> parked (<links>)
- Worktrees: <removed / left at <path> on <branch>>
- Pushed: <sha> to <branch>  |  Comm: `ack: <role> stood down` posted
- Working tree: nothing of mine left dirty  |  Heartbeat: left in place, now stale
- Unmonitored from now: <env — what to watch>  |  or: nothing was monitored by this role
- To resume: paste `<prompt>` into a fresh session, `/model <tier>`, `/loop <interval>s`
```

If any verification came back non-empty, say so plainly and name what is still open —
a stand-down reported as clean when it is not is worse than no stand-down at all.
