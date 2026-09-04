# Codex adapter runtime

The host adapter carries the host call; it does not add workflow authority.
Lead supplies one bounded Input, a specialist performs the Process, and the
specialist returns one Handoff. Direct native spawning is valid when the host
payload is already known.

## Native payload

The optional `prepare-dispatch.py` formatter accepts a role (or a native
`agent_type`) and a plaintext `message`/`objective`, then emits:

```json
{"agent_type":"worker","task_name":"worker_ab12cd34","fork_turns":"1","message":"..."}
```

It may add `model` and `reasoning_effort` only when those options are explicitly
provided. `task_name` and `fork_turns` bind the active host call but do not create
workflow authority; callers may skip the formatter for a direct
`collaboration.spawn_agent` call. Receipts, timing, admission decisions, and
other removed ceremony remain rejected.

## Roles and concurrency

Use canonical role cards under `core/roles/`. Keep at most two ordinary
specialists active, with one writer per file and no nested delegation. Lead
owns status and routes a handoff to the next related role. Code Reviewer, Test
Engineer, and Gatekeeper are independent risk-triggered roles; mutation
invalidates only evidence affected by the changed bytes.

## Watchdog

Run `scripts/stuck-watchdog.py` only around a real background command. It emits
internal completion, failure, or timeout status and never retries, selects a
role/model, approves, or advances a task. A watchdog status is not a handoff.

## Installation

`scripts/check-install.py` verifies the installed root, links, platform, and
required entrypoints. `ACTIVE` means those bindings are present; `INACTIVE`
means revalidation or activation is needed. Neither status proves execution,
product validation, or release readiness.
