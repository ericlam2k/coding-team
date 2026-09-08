# Orchestration

Coding Team uses one default flow:

```text
Input → Process → Handoff → related role
```

The Lead routes work. One accountable role performs each task. A handoff is the
single semantic record of the result. Tools support the work; they do not create
a second workflow.

## Input

A task needs only:

- accountable role;
- objective and acceptance;
- owned write paths and relevant read paths;
- focused check;
- stop condition.

If product meaning or an irreversible decision is missing, ask for it. Otherwise
the Lead routes the task without a separate admission ceremony.

## Process

The assigned role performs the work directly.

- One owner per task and one writer per file.
- Use the smallest useful skill and check.
- Do not spawn another role from inside a specialist task.
- Split only when concerns, owners, or write paths genuinely conflict.
- Prefer a fresh specialist context so Lead instructions do not become worker
  behavior.

WIP of two ordinary specialists is a planning default, not a reason to block a
ready single task.

## Handoff

The handoff is the task record. It states:

- status and conclusion;
- changed artifacts or decision;
- evidence from the focused check;
- residual risk or blocker;
- recommended next role or action.

No machine log or host formatter replaces the handoff.

After the accountable role finishes, the same task and thread writes the short
`templates/handoff.md` record. Use the cheapest capable mapped slug for that
wrap-up. Do not spawn another role, and do not open a new Task only to change
model.

Docs Steward writes only a named durable documentation artifact others will
reuse. It does not write ordinary task records.

Lead may write the handoff from the worker's facts without a spawn, then route
from that record. A hard stop does not reset by hopping models.

## Related-role routing

The Lead chooses only the next role that answers an unresolved question.

| Need | Related role |
|---|---|
| Product scope or acceptance | `product-manager` |
| Shared technical contract | `system-architect` |
| Technical direction | `advisor` |
| Material challenge | `contradictor` |
| Repository facts | `investigator` |
| Server, API, or persistence work | `backend-engineer` |
| Journey or UX contract | `frontend-ux-lead` |
| UI implementation | `frontend-builder` |
| Built UI vs named UX contract | `frontend-ux-lead` |
| Built API/data vs frozen architecture contract | `system-architect` |
| Integration of a frozen contract | named builder as FIO (hat, not a role) |
| Independent code inspection | `code-reviewer` |
| Executable behavior evidence | `test-engineer` |
| Durable documentation | `docs-steward` |
| Material final acceptance or release | `gatekeeper` |

Code Reviewer, Test Engineer, and Gatekeeper are independent capabilities, not a
mandatory chain for every task. Use each only when its question exists.

Do not merge these three questions: contract (before build), built vs contract
(after build, when a named UX or architecture contract existed), and material
accept/release (Gatekeeper). Gatekeeper does not replace Frontend UX Lead or
System Architect on the running UI or API.

FIO is a temporary hat on one builder after Architect froze a contract, not a
role ID. Frontend Builder owns a frontend seam; Backend Engineer owns an
API/data seam. Drift routes **FIO → Lead → System Architect**.

## Risk

Lead records `small`, `standard`, or `high` on the Input only when it changes
the route. Risk omits or adds questions; it never skips the contract owner.

| Risk | Built vs contract | Reviewer / Test Engineer | Gatekeeper |
|---|---|---|---|
| `small` — single-owner, no named UX/API contract | Skip | Skip when the focused check proves the outcome | Skip |
| `standard` — named UX or architecture contract | Same owner reviews the built UI/API | Only if bytes or behavior remain unproven | Only if this is still a material accept/release |
| `high` — security, privacy, migration, public contract, 2+ layers, mutation/state, or costly reversal | Same owner reviews the built UI/API | Usually yes | Yes |

`risk: high` on an Architect or backend Gatekeeper packet selects a stronger
model. It is not Builder → Gatekeeper and not a reason to drop UX or Architect.

Contract-fidelity **judgment** stays on the contract role. Browser clicks,
screenshots, HTTP/log probes, and other mechanical evidence use the cheapest
capable mapped slug (`frontend-ux-lead:inspect`, `system-architect:inspect`,
or tier 0). Do not inherit the GLM/Sol/Fable contract slug for that tool loop.
Prefer the builder's already-captured states; replay the browser or API only
when that evidence is missing. This is an in-role phase change, not a new
role, and not Test Engineer.

## Lead responsibility

The Lead:

1. converts the request into one clear Input;
2. routes it to the accountable role;
3. reads the Handoff;
4. resolves or routes the remaining question;
5. stops when the requested outcome is proven.

A failed or partial task returns to Lead for the smallest correction or
rerouting. It does not automatically require a new gate, model change, or
workflow restart.

## Completion truth

Mark work `complete` only when the requested outcome is actually true and its
named acceptance evidence exists. A proposal, policy document, packet `READY`,
installed symlink, or passing narrow check is not completion unless it proves
the requested behavior. State any unavailable route, inherited host default,
missing execution identity, unrun check, or remaining approval as `PARTIAL` or
`BLOCKED`; never hide it behind a completion claim.

## Optional execution support

- Use the watchdog only for a real background or long-running command that needs
  a deadline and cancellation.
- Use additional QA evidence tooling only when a named release, security,
  privacy, migration, or audit requirement demands it.
- Host adapters may format native spawn calls, but host-schema checks are not
  core policy and never prove worker completion.
- Install checks prove activation only; they never prove task execution.

## Human gates

Human approval is required for destructive operations, production deployment,
secrets, new dependencies or services, public-contract breaks, and material
scope expansion. Ordinary in-scope implementation, correction, focused tests,
and role routing proceed without repeated approval.

## Platform boundary

Core remains host-neutral. Host-specific spawning, cancellation, and model
options belong under `adapters/<host>/`.
