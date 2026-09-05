# Codex adapter runtime

The host adapter carries the host call; it does not add workflow authority.
Lead supplies one bounded Input, a specialist performs the Process, and the
specialist returns one Handoff. Direct native spawning is valid when the host
payload is already known.

## Native payload

`prepare-dispatch.py` uses one bounded selector for two verified direct host
schemas. The caller attests exactly one visible binding with `mode` set to
`direct_tool_call`, `available_to_caller` set to `true`, and no extra keys:

```json
{"tool":"collaboration.spawn_agent","mode":"direct_tool_call","available_to_caller":true}
{"tool":"multi_agent_v1__spawn_agent","mode":"direct_tool_call","available_to_caller":true}
```

Historical V1 `collaboration.spawn_agent` emits exactly `task_name`,
`agent_type`, `fork_turns`, `message`, `model`, and `reasoning_effort`. Current
V2 `multi_agent_v1__spawn_agent` emits `agent_type`, `fork_context`, and
`message`; `model` and `reasoning_effort` appear only when explicitly supplied
by the caller. V2 always emits `fork_context=false` for a fresh specialist and
rejects caller-supplied `fork_context`, `task_name`, or `fork_turns`.

Missing, malformed, false, extra-key, unknown, indirect, or mixed bindings
return `BLOCKED` with no spawn. `functions.collaboration.spawn_agent`,
`functions.exec`, `exec_command`, `tools.*`, shell, Python, Node, JavaScript,
and nested tool bindings are not direct bindings. There is no schema probing,
post-READY translation, fallback, or dual dispatch.

READY proves packet-valid plus selected direct-binding-attested preflight only;
it does not prove host acceptance, child start, supervision, or completion.
For V1: Invoke the direct collaboration.spawn_agent tool exactly once with
READY.spawn; do not use functions.exec, exec_command, shell, JavaScript, or a
nested tool binding. For V2: Invoke the direct multi_agent_v1__spawn_agent tool
exactly once with READY.spawn; do not translate fields, retry, or use
functions.exec, exec_command, shell, JavaScript, or a nested tool binding.

Top-level `binding` and deterministic `dispatch_id` are correlation metadata,
never host payload or execution proof. A successful V2 response must provide
authoritative `agent_id`; `nickname` is informational. Missing, rejected,
timed-out, or ambiguous responses are no execution evidence and permit no
automatic retry. Receipts, timing, admission decisions, and other removed
ceremony remain outside this lean formatter.

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
