---
name: coding-team
description: Lean Coding Team workflow for Codex.
metadata:
  short-description: Input to Process to Handoff routing for Codex
---

# Coding Team (Codex)

Lead is the workflow owner. The canonical flow is:

```text
Input → Process → Handoff → related role
```

Read `core/orchestration.md`, `core/model-routing.md`, `core/concurrency.md`,
and `core/human-gates.md`, then read only the role card needed for the current
task. Keep WIP at two ordinary specialists or fewer; there is no supervisor
lane. A specialist owns its task and does not spawn another role.

Code Reviewer, Test Engineer, and Gatekeeper are independent, risk-triggered
capabilities. Use the smallest one that answers the unresolved question, and
rerun only evidence affected by a mutation. A handoff is the single semantic
task record; it states status, conclusion, changed artifacts, focused evidence,
residual risk, and the recommended next role or action.

## Optional native host formatting

`adapters/codex/scripts/prepare-dispatch.py` is a convenience formatter, not a
gate or admission step. It returns only:

```json
{"agent_type":"worker","fork_context":false,"message":"..."}
```

`model` and `reasoning_effort` are included only when explicitly requested.
There is no task name, context-depth field, host attestation, timing envelope,
receipt, or required formatter call. Call `collaboration.spawn_agent` directly
when the host payload is already available.

## Watchdog

Use `stuck-watchdog.py` only for a real background command that needs a bound.
Its status is an internal completion, failure, or timeout log; it never routes,
retries, approves, or creates workflow authority.

## Installation

`check-install.py` verifies the installed root, links, platform, and required
entrypoints. It reports `ACTIVE` or `INACTIVE`; activation is not task or
product acceptance. Product validation remains the consumer project's job.
