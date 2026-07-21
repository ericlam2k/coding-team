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

## Incomplete → stop for human

Stop and ask the human when any of these occur:

- Role output is **incomplete**, malformed, or missing required fields
- Gatekeeper returns **non-APPROVE** (REVISE / BLOCK)
- Advisor and Contradictor **deadlock** on material risk and Lead cannot resolve without policy trade-offs
- Evidence is missing, conflicting, or cannot be reproduced
- A required gate was skipped or the brief contradicts these rules
- The worker would need to invent product preference, secrets, or out-of-scope roles

Do **not** paper over gaps with assumptions. State **what** you need, **why**, and **where** the human can decide or provide it.

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
