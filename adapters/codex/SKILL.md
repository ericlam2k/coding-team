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

## Native host formatting

`adapters/codex/scripts/prepare-dispatch.py` uses one bounded selector for two
verified direct schemas. Attest exactly one visible binding with
`mode=direct_tool_call`, `available_to_caller=true`, and no extra keys:

```json
{"tool":"collaboration.spawn_agent","mode":"direct_tool_call","available_to_caller":true}
{"tool":"multi_agent_v1__spawn_agent","mode":"direct_tool_call","available_to_caller":true}
```

Historical V1 `collaboration.spawn_agent` emits exactly `task_name`,
`agent_type`, `fork_turns`, `message`, `model`, and `reasoning_effort`. Current
V2 `multi_agent_v1__spawn_agent` emits `agent_type`, `fork_context`, and
`message`; `model` and `reasoning_effort` appear only when explicitly supplied.
V2 emits `fork_context=false` for a fresh specialist and rejects caller-supplied
`fork_context`, `task_name`, or `fork_turns`.

Missing, malformed, false, extra-key, unknown, indirect, or mixed bindings
return `BLOCKED` with no spawn. Reject `functions.collaboration.spawn_agent`,
`functions.exec`, `exec_command`, `tools.*`, shell, Python, Node, JavaScript,
and nested tool bindings. Never probe, translate between bindings, fall back,
or dual-dispatch.

READY proves packet-valid plus selected direct-binding-attested preflight only;
it does not prove host acceptance, child start, supervision, or completion.
For V1: Invoke the direct collaboration.spawn_agent tool exactly once with
READY.spawn; do not use functions.exec, exec_command, shell, JavaScript, or a
nested tool binding. For V2: Invoke the direct multi_agent_v1__spawn_agent tool
exactly once with READY.spawn; do not translate fields, retry, or use
functions.exec, exec_command, shell, JavaScript, or a nested tool binding.

Top-level `binding` and deterministic `dispatch_id` are correlation metadata,
not host payload or execution proof. A successful V2 response requires
authoritative `agent_id`; `nickname` is informational. Missing, rejected,
timed-out, or ambiguous responses permit no automatic retry. The handoff
remains the workflow record; removed admission, timing, supervisor, and receipt
ceremony stays outside this lean formatter.

## Watchdog

Use `stuck-watchdog.py` only for a real background command that needs a bound.
Its status is an internal completion, failure, or timeout log; it never routes,
retries, approves, or creates workflow authority.

## Installation

`check-install.py` verifies the installed root, links, platform, and required
entrypoints. It reports `ACTIVE` or `INACTIVE`; activation is not task or
product acceptance. Product validation remains the consumer project's job.
