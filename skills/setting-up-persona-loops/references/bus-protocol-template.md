# Work-item bus — PROTOCOL.md template

Create `docs/<bus>/` with `PROTOCOL.md` (this file, adapted), `next/`, `done/`
(add `.gitkeep`). The bus carries **work items only**; narrative journals live
elsewhere. No validator script in v1 — PROTOCOL.md is the schema; sessions validate
by reading it.

Replace the role list and the `type` enum with your own. Keep the rules verbatim
unless a rule provably does not apply — each one was added after a failure.

---

```markdown
# <Loop name> — Work-Item Protocol

The machine-readable bus between the <N> loop sessions (<role list>) and the
user. Design: `<spec path>`.

**Scope:** <app path>/** and its operational surface. <Other app> is out of
scope for every role here; its own personas live in `docs/operation/<other>/`
and take no items from this bus.

## Layout

- `next/` — open items.
- `done/` — finished items (moved here with an `## Outcome` section).

The bus is not the pod's chat. What a neighbour needs *this wake* — a guide
changed, a required persona is down, a breach — goes to the shared comm
(`docs/operation/<app>/comm/`, transient, pruned after 7 days); the bus
carries work items with a status and edit rights.

## Filename

`YYYY-MM-DD-NN-to-<role>-<slug>.md`

- `NN`: two-digit per-day sequence, unique across `next/` **and** `done/` for
  that date. Re-list both directories immediately before filing — concurrent
  sessions collide on NN otherwise. (If several roles file at the same
  moment often, use the UTC time `HHMM` instead of `NN`; it needs no re-list
  and still sorts.)
- `<role>`: `<r1>` | `<r2>` | `<r3>` | `user`. Tokens are short and
  none is a prefix of another (so `to-<r1>-` globs never sweep `to-<r2>-`
  items). Never add a longer synonym for an existing token.

When filename and frontmatter disagree, **the frontmatter `to:` wins** — fix
the filename.

## Frontmatter (required, exactly these keys)

```yaml
---
from: <r1> | <r2> | <r3> | user
to: <r1> | <r2> | <r3> | user
type: <proposal> | <tuning> | data-need |
      bug-report | feature-request | soak-request |
      soak-report | live-report | approval-request | ops-issue
status: todo | in-progress | approved | done | rejected
priority: P1 | P2 | P3
created: YYYY-MM-DD
---
```

Body: what/why, acceptance criteria, links to reports/plans/data — plainly
stated, no more than the receiving role needs (`*-loop-prompt.md` → "Write
tight"). Items must be self-contained — the receiving session acts without
the author being alive — so spell out in full the exact command, value, sha
and acceptance criterion it must act on. That detail is the item's payload.

**Priority is P1/P2/P3 — there is no P0.** "Drop everything" is a P1 that says
so in the body and sorts first within P1; any other token is malformed (rule 6).

## Rules

1. **Edit rights.** Only the **addressed** role (`to:`) changes `status`; only
   the **author** (`from:`) edits the body after filing. Exception:
   `status: approved` on a `to-user` approval-request may be set **only by the
   human user**. Once approved, the <executing role> executes the item and is
   the one that moves it to `done/` with the execution `## Outcome`.
2. **Lifecycle.** `todo` → `in-progress` (claim, commit) → `git mv` to `done/`
   with `## Outcome` appended and `status: done` (or `rejected`, with the
   reason). Outcomes are numbers, shas, verdicts, the verification command
   and its result — never just "done" and never narration
   (`*-loop-prompt.md` → "Write tight"). **One item never spans two roles.**
   When one role's part is finished, its item is `done` and the next step is
   a **new** item addressed to the next role. Holding an item open waiting on another role hides it
   from the staleness rule.
3. **Approval-requests** name the exact sha, the exact config diff (every
   changed `KEY=VALUE` line), the cost cap, and the transition. Anything
   ambiguous fails closed: the executor rejects and asks instead of guessing.
4. **Publish immediately.** Every session syncs at cycle start with
   `git fetch -q origin && git merge --ff-only origin/main` (never
   `pull --rebase`: it refuses whenever any file in a shared checkout is
   dirty and silently skips the sync) and commits its bus changes right away
   in bus-only commits (message prefix `journal:`), **naming the paths**
   (`git commit -- <paths>`; never `add -A` / `commit -a`) so a shared
   checkout's stray changes stay untouched. The guard hook in the persona
   recipe refuses the broad forms.
5. **Staleness.** An `in-progress` item untouched > 24 h is flagged by
   whichever session notices, as a `to-user` `ops-issue`.
6. **Malformed items** (bad frontmatter, missing acceptance criteria, wrong
   addressing) → `status: rejected` with the reason. Never guess.
7. **Routing — address by who is allowed to do the work.**
   - Needs a **code change** to fix a defect (bug, test, migration file) →
     `to: <eng>`.
   - Asks for a **feature** (new or changed behavior) → `to: <pdm>` when a
     product-manager persona exists; it cuts, shrinks, or forwards `to: <eng>`
     with the need and the smallest scope. Without one, `to: <eng>`.
   - **Removes shipped behavior**, a whole feature, or a persona → `to: user`
     proposal (from the product manager, with evidence); never straight to
     the engineer.
   - Needs an **env/config change, deploy, restart, or safety toggle** →
     `to: <that env's operator>` (or `to: user` where the env is user-gated).
     The engineer may not do any of these; a `to-<eng>` item asking for one is
     malformed under rule 6. Such an item states the **exact** value to set
     and **how to verify** it took effect.
   - Needs **analysis of recorded data** → `to: <research>`.
   - Work large enough for its own plan-and-execute session → `to: user`
     `feature-request`, saying what makes it large.

## Who files what

| From → To | Types |
|-----------|-------|
| research → eng | proposal, tuning, bug-report |
| research → pdm | feature-request |
| research → <env op> | data-need (capture/lever asks the operator owns) |
| user → eng | proposal, tuning, bug-report |
| user → pdm | feature-request |
| <env op> → eng | bug-report (anything needing a code fix) |
| <env op> → pdm | feature-request |
| pdm → eng | feature-request (shrunk: `## Need`, `## Cut`, acceptance criteria) |
| pdm → user | proposal (remove shipped behavior / feature / persona; retire a type, gate, rung) |
| prod → eng | bug-report (prod-observed defects) |
| eng → <env op> | soak-request (merged sha to deploy + soak), lever asks |
| eng → user | feature-request (too large for a routine cycle) |
| eng → research | data-need (evidence to settle a diagnosis) |
| <env op> → user | approval-request (promotion, after a passing soak) |
| <env op> → research | soak-report (also on failure — it feeds research) |
| prod → research | live-report |
| any → user | ops-issue |
```

---

## Item skeleton

```markdown
---
from: <role>
to: <role>
type: <type>
status: todo
priority: P2
created: YYYY-MM-DD
---

# <Title: the symptom or the ask, with the number that makes it concrete>

## What / why
<Context, evidence: exact queries, log lines, timestamps, shas.>

## Acceptance criteria
1. <Observable, checkable.>
2. <…>

## Links
<Reports, plans, related items.>
```

Closing appends:

```markdown
## Outcome

<Merged sha / deployed sha / measured numbers / verdict; the verification
command and its result; what was handed to whom as which new item — no
narration.>
```
