# Human gates

Explicit human approval is required before irreversible or high-risk work. **Silence is never approval.**

## Approval before implement / operation

Require a clear human yes (chat message, checkbox, or signed brief field) before:

| Gate | Examples |
|---|---|
| **Start high-risk implement** | Nature N5 after Advisor/Contradictor; irreversible schema/data changes; auth/privacy redesign; public contract break |
| **Destructive ops** | Force push, hard reset, mass delete, production data wipe, secret rotation |
| **Dependency / infra** | New package or service; production deploy; permanent environment change |
| **Scope expansion** | Work outside the admitted sprint/batch brief |
| **First release of a surface** | Shipping a new public endpoint, UI journey, or migration to production |

Low-risk N0/N1 work inside an already-admitted batch does not need a fresh gate per task unless the brief or host install adds one.

## Task progression inside an admitted Batch

A valid Task handoff may advance to the next dependency-safe Task already named
in the admitted Batch without another human approval. Valid means the canonical
owner returned `DONE` or `COMPLETE`, stayed inside owned paths, supplied the
declared artifact and checks, and reported blockers and residual risk. This is
Task completion only. It is not Batch acceptance and does not authorize commit,
push, deploy, release, or another Batch. Reviewer routes are defined only in
[`qa-operating-model.md`](qa-operating-model.md); normal scope-expansion and
irreversible-action gates still apply.

Stop immediately for `PARTIAL`, `FAILED_TRANSIENT`,
`FAILED_TRANSIENT_CONTEXT`, `BLOCK`, `BLOCKED`, `needs_decision`, a missing or
malformed handoff, failed declared checks outside the canonical QA evidence
route, unowned mutation, conflicting or stale evidence, or any required gate.
Do not retry, substitute a model, invent a correction, or admit a new Batch
automatically.

A terminal-closeout validator failure stops progression. Lead may request one
format-only closeout correction from the same named owner; it is not a retry or
a new Task. If that correction needs a decision, new evidence, a different
owner, or new scope, stop for the human instead.

Also stop when:

- Advisor and Contradictor **deadlock** on material risk and Lead cannot resolve without policy trade-offs
- Evidence is missing, conflicting, or cannot be reproduced
- A required gate was skipped or the brief contradicts these rules
- The worker would need to invent product preference, secrets, or out-of-scope roles

Do **not** paper over gaps with assumptions. State **what** you need, **why**, and **where** the human can decide or provide it.

## Production vs preview

**Production** deploy, first preview/staging admit, commit/push/merge (unless pre-authorized), secrets, and destructive ops always need an explicit gate.

Optional host/project overlay: once a **preview** surface is already admitted for the active batch, in-session UI/product feedback may follow a fix → local smoke → preview redeploy → show URL loop without re-asking for that same preview. That overlay **never** authorizes Production, first preview admit, commit/push, secrets, or scope expansion.

## Silence ≠ approval

| Not approval | Is approval |
|---|---|
| No reply | Explicit “approve / yes / proceed / ship” tied to the ask |
| “Looks fine” on unrelated topic | Named decision on the gated action |
| Prior sprint approval | Fresh yes for a new irreversible op |
| Auto-merge / default settings | Human message in-session (or documented signed gate) |

If unclear, **ask again**. Do not proceed on ambiguity.

## Conversation while a gate is pending

A human gate pauses the governed action and workflow mutation; it does not
pause conversation. Do not require the human to know or type command keywords.
Interpret the semantic intent of natural language in the current task context.
The categories below are internal handling rules, not user commands:

- A question or request for an example or explanation is answered immediately
  with **zero workflow mutation**, and the gate remains pending. Quoted approval
  wording, including a request for an approval example, is not approval.
- Approval resumes only when an explicit human message is bound to the current
  task, gated action, and scope. Resume only the approved action; unrelated
  gates and later actions remain pending.
- A clear request to revise or cancel changes only the named current decision.
  Do not infer approval or alter unrelated tasks, scope, gates, or release state.
- Ambiguous input receives a concise clarification question with zero workflow
  mutation, and the gate remains pending.

## After approval

- Record the gate decision in the batch checkpoint or handoff (`who`, `what`, `when`).
- Implement only the approved scope; new risk → new gate.
- A valid completed Task may advance only through the pre-admitted Batch queue.
  Any stop condition above returns to the human; approval to start is not
  approval to ship broken work.
- A proposed commit message (when requested) never authorizes staging, commit, push, merge, or changing the staged set.
