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

## Incomplete / non-complete output (mid-batch)

Required when any coding-team task or batch returns output that is **not** accepted completion: anything other than Gatekeeper `APPROVE` / `APPROVE_WITH_NOTES` with batch `COMPLETE` (or an explicitly human-accepted residual-risk exception).

Includes: `PARTIAL`, `FAILED_TRANSIENT`, `FAILED_TRANSIENT_CONTEXT`, `REVISE`, `BLOCK`, `needs_decision`, empty/malformed deliverables, missing cleanup evidence, Test Engineer pass without Gatekeeper, or informative dry-run output that is not accepted.

**Lead must stop and ask the human for the next step** before launching another coding-team task (except the single already-admitted retry in the active brief). Do not auto-chain fixes or admit a new batch without that gate.

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

## After approval

- Record the gate decision in the batch checkpoint or handoff (`who`, `what`, `when`).
- Implement only the approved scope; new risk → new gate.
- Incomplete/non-APPROVE after the gate still stops for human — approval to start is not approval to ship broken work.
- A proposed commit message (when requested) never authorizes staging, commit, push, merge, or changing the staged set.
