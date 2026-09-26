# Shared comm — README template

Create `docs/operation/<app>/comm/README.md` from this. Day-files appear on
first use. The comm exists next to a bus or without one; it is not a bus:
the bus carries work items with status and edit rights, the comm carries
what a neighbour needs within a wake and is deleted after a week.

---

````markdown
# Shared comm — the pod's transient channel

The **pod** is the set of live persona sessions of the <app>: the
**<operator>** and the **<engineer>** (required — the loop is live only when
both heartbeats are fresh) and <optional roles> (optional). This directory is
how pod members talk to each other between wakes. It is **transient**: one
file per day, entries appended, and the operator deletes any day-file older
than 7 days. Anything that must outlive a week goes where it belongs — a rule
into a guide, a fact into the ledger, work into a task file or bus item.
Nothing here is a claim, a status of record, or a decision.

## Files

`YYYY-MM-DD.md`, local date (<TZ>). The first writer of the day creates it
with the heading `# Comm — YYYY-MM-DD`. Append-only: never edit or delete
another persona's entry. Tracked in git so a fresh session sees it — commit
at once, named paths only, prefix `comm:`.

## Entry

```markdown
## HH:MM <from> → <to> · <kind>: <subject>
One to three lines: what happened, why. No "it is X, not Y" framing, no
elaboration beyond that (`*-loop-prompt.md` → "Write tight"). Name paths and
shas. Never a secret, an account number or a dollar figure.
```

**A sha you name must be on `main`** — check it
(`git merge-base --is-ancestor <sha> main`) before posting. A worktree
branch's sha frequently does not survive its merge, so the commit you just
watched can be unreachable from `main` minutes later and the entry sends
every reader to a `git show` that fails. This bit on day one of the protocol
in the loop it was extracted from: two shas, one tree, three entries naming
the branch one.

`from` / `to`: `<role tokens>` | `user` | `pod` (everyone live).

| kind | it says | the receiver does |
|---|---|---|
| `guide-update` | a persona guide (`docs/operation/<app>/*-loop-prompt.md`) changed; the body names the file(s) and the sha | the named persona **re-arms**: re-reads its whole guide from disk in that wake, re-runs its liveness/RE-ARM section against the new text, posts `ack` |
| `shutdown` | the user is closing the pod; the body names who (`pod`, or the roles) and from when | the named persona stands down **in that wake**, ahead of its other work — park claims, `CURRENT STATE`, journal, push — then posts its `ack` and stops. The operator goes **last**: it collects the acks, files what nobody could close, posts `note: pod down` |
| `ack` | `<role> re-armed at <sha>`, or `<role> stood down at <HH:MM>` | nothing — but a neighbour whose stood-down ack you have seen is **stood down, not `down`**: post no `down` for it |
| `down` | a required persona is not looping — its heartbeat is **absent** (never armed with `/loop`; report at once, no second test) or **stale** (older than the window **and** no commits since) | the user re-arms it (paste the guide into a fresh session, then `/loop <interval>`); no persona restarts another |
| `breach` | a shared-checkout or claim-protocol breach, with the commit | the offender appends the dated trap to its own guide; the catcher has already recorded where the content landed |
| `handoff` | a one-off ask between personas that is not a task or bus item — a fact, a question, "your file moved" | reply as `note`, or file the item |
| `note` | anything else worth one wake of attention | read |

## Reading

Every wake, after the git sync: read today's and yesterday's files and act on
entries addressed to you or `pod` that are newer than
`~/.<app>/<role>-comm-read` (the `YYYY-MM-DD HH:MM` of the last entry you
processed; write it after acting). No record → read both files in full.

## Custody (operator)

- Each cycle, `git rm` every day-file older than 7 days and commit
  (`comm: prune <dates>`).
- An unannounced guide change — a commit touching a `*-loop-prompt.md` with
  no matching `guide-update` here — gets its entry posted by the operator on
  the author's behalf
  (`git log --since=<last check> --format='%h %s' -- docs/operation/<app>/*-loop-prompt.md`).
````
