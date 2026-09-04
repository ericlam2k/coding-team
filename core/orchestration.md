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
| Independent code inspection | `code-reviewer` |
| Executable behavior evidence | `test-engineer` |
| Durable documentation | `docs-steward` |
| Material final acceptance or release | `gatekeeper` |

Code Reviewer, Test Engineer, and Gatekeeper are independent capabilities, not a
mandatory chain for every task. Use each only when its question exists.

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
