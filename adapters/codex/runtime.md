# Codex runtime — role delegation

Lead (this skill) classifies nature, writes a ≤250-word run prompt, and spawns **one** Codex subagent per task. Each spawned specialist is the sole worker for that Task: it performs the brief itself, never delegates or spawns another agent, and writes only to the declared owned paths. Prefer independent subagents with the mapped model/effort from `model-pool.map.md`.

## Adaptive admission before preflight

Resolve `ADMIT` from `core/adaptive-timing.md` before running
`prepare-dispatch.py`; only `ADMIT` continues to the preflight. Use the current
named approved profile or its labeled fallback. Price required policy, memory,
migration, repository bootstrap, and context reload as setup. Add the bounded
mutation units, every validation command, checkpoint/handoff work, and
`T_reserve`. No fixed target, checkpoint, hard stop, or reserve is universal.

The Lead must pre-resolve each named contract, test, evidence reference, and
dependency needed by the worker. Reserve and publish the checkpoint or handoff
identity before mutation so a hard stop cannot erase task identity. Discovery
hidden inside a mutation packet is unpriced work and fails admission.

If measured evidence shows a fresh nested route consumed the useful window,
the unchanged fresh route is `BLOCK`; do not retry it or hop models. First poll
the live handle or verify terminal state, then reconcile the declared artifact
paths as `COMPLETE`, `PARTIAL`, or `NO_PROGRESS` and persist that checkpoint.
Prefer a safe same-task context continuation with exactly one material
plaintext delta when task identity, scope, permissions, policy, and evidence
remain current. Do not mirror the initial packet. Otherwise shrink the
Task and pre-resolve its setup in a bounded `MEASURE` task before a
new dispatch. Escalate only when the corrected route changes authority, scope,
risk, provider, or another human gate.

A critical correction may use native context continuation only as a
human-approved one-off `ACCEPTED_RISK` when evidence demonstrates that
supervised bootstrap, rather than mutation or validation, is the blocker. The
exception retains the stop condition and handoff-first discipline; it is not a
default critical runner and does not waive a later clean Test Engineer →
bounded QA evidence validator when triggered → Gatekeeper sequence. Later
fresh nested tasks still require the supervised runner when the host has no
verified deadline supervisor.

## Mandatory pre-dispatch preflight

Every Coding Team spawn must pass the Codex adapter preflight before the host
spawn call. The Lead supplies a structured JSON object with:
`role`, `task_id`, `objective`, `acceptance`, `paths`,
`validation`, `stop`, `model`, `effort`, and an allocation with
`candidate_changed_paths` and `prior_hard_stop`. For an explicit canonical
role, set the host-required `fork_turns` to `"1"` only. `fork_turns` is a host
context transport field, not a subagent count; larger inherited contexts are
blocked because they can re-enter Lead routing. The current host contract does
not represent a verified zero-context mode, so deleting the field would trade
context leakage for host rejection.
`fork_context`, `none`, `all`, omitted, boolean, zero, negative, and malformed
depths are rejected rather than silently changing context, model, or reasoning
semantics. Never pass a raw packet or opaque brief to the direct
`collaboration.spawn_agent` tool. Opaque,
encrypted-only, missing, non-canonical, or out-of-scope values fail closed.

The packet's `host_binding` must also carry this exact preflight attestation:
`{"tool":"collaboration.spawn_agent","mode":"direct_tool_call","available_to_caller":true}`.
It means only that the current parent context exposes the named direct binding.
Missing, false, malformed, extra-key, or indirect bindings return `BLOCKED`;
the diagnostic is: run preflight from a parent context that exposes direct
`collaboration.spawn_agent`, then invoke it directly; no indirect fallback
exists. Do not substitute `functions.collaboration.spawn_agent`, `functions.exec`,
`exec_command`, `tools.*`, shell, Python, Node, JavaScript, or nested bindings.

Keep candidate-wide identity checks outside a narrower worker validation
list. `MEASURED` timing units require an evidence reference. `ESTIMATED`
returns `MEASURE`; a prior hard stop returns `BLOCK`.

Run the guard from the Coding Team checkout, for example:

```bash
python3 "$CODING_TEAM_ROOT/adapters/codex/scripts/prepare-dispatch.py" \
  --input /path/to/dispatch-packet.json \
  --coding-team-root "$CODING_TEAM_ROOT"
```

Only a `READY` result may be passed to the host. `READY` means packet-valid plus
direct-binding-attested preflight only; it does not prove host acceptance,
child start, supervision, or completion. Its `spawn` object uses exactly
`task_name`, `agent_type`, `fork_turns`, `message`, `model`, and
`reasoning_effort`. `task_name` is derived deterministically from canonical
`task_id` plus `dispatch_id`; callers never supply it. The message is capped at
250 words and names the absolute
canonical role-card path with an instruction to read it first. `BLOCKED`
results have no usable spawn packet; Lead stops and corrects the brief rather
than dispatching an encrypted blob or retrying the same malformed packet.

The result also carries a deterministic `dispatch_id`. Prefer
`dispatch_id + agent_thread_id + call_id` as the evidence identity. When the
host omits `agent_thread_id` or `call_id`, require `dispatch_id + deterministic
task_name + the authoritative single spawn response`; explicitly record each
unavailable thread/call identifier and whether the host model receipt is
unavailable. Invoke the returned `spawn` object once. Do not mirror the initial
objective through `send_message` or `followup_task`; reserve those operations
for a new material plaintext delta or a requested correction. This follows the
standard at-most-once delivery and idempotency-key pattern. Never use Codex UI
activity rows as run, retry, token, cost, model, or identity evidence.

The top-level `READY` result also carries `invocation` guidance outside the
six-key `spawn` object:
`Invoke the direct collaboration.spawn_agent tool exactly once with READY.spawn; do not use functions.exec, exec_command, shell, JavaScript, or a nested tool binding.`
The guidance is not forwarded to the worker. Invoke `READY.spawn` exactly once;
the direct host response and child artifact/handoff remain the execution
authority.

This is a Codex-adapter guard, not host enforcement. The assertion cannot prove
that a host consumed the role card, accepted the model route, or prevent a
caller from bypassing this script through another spawn entry point. It cannot
patch or alter the host collaboration API. Host/runtime receipts remain the
authority for actual model use and role-card consumption.

The generated worker message adds a specialist boundary: the child is the sole
worker; do not spawn, delegate, or orchestrate another agent. It may write only
to the listed owned paths; all other paths are read-only. If required work falls
outside those paths, it must stop and report `BLOCKED`. This is instruction-level
containment; direct host spawning cannot sandbox file writes. Mutation-sensitive
tasks should use the supervised critical-task runner, whose terminal receipt
rejects unhanded paths.

## Bounded STUCK supervision

When the host exposes no equivalent deadline supervisor, run one admitted task
through `scripts/stuck-watchdog.py`. It requires task/run identity and
`0 < target < hard_stop`, emits one `CHECKPOINT`, and cancels the child at the
hard stop. It writes one terminal `COMPLETED`, `FAILED`, or `STUCK_REPORT`
receipt. `STUCK_REPORT` is `BLOCKED`, sets `retry_allowed=false`, and names one
smaller next action. It never retries, changes model/role, approves a gate, or
advances workflow itself. Lead reconciles authoritative state and may admit a
materially changed smaller route under `core/adaptive-timing.md`. This is
adapter-local; raw host calls can still bypass it.

## Framework reload after compaction

Read `framework-reload.md` after every compaction or new session. The global
skill rule requires explicit reload unless an official host receipt proves the
compact lifecycle and restored context. The adapter cannot install or mutate
project hook configuration through this dispatch guard.

## Delegation table

| Canonical role | When to spawn | Codex pattern | Tier (look up map) | Notes |
|---|---|---|---|---|
| `investigator` | N0 map/fact; N2/N5 pre-scan | Subagent, read-mostly | 0 (1 if cross-file) | Path/line evidence only; no edits |
| `monitor-agent` | Frozen supervisor-relay observation only | Subagent, read-only + one create-once relay artifact | 0 | No candidate mutation, sibling control, quality verdict, or host-process authority |
| `advisor` | N2/N4/N5 direction | Subagent, read-only | 2 | Pre-build verdict; never implements or Gatekeeps |
| `contradictor` | Required N2/N4/N5 debate | Subagent, read-only | 2 | **Serial after Advisor**; never parallel with Advisor under WIP |
| `product-manager` | Ambiguous product scope | Subagent | 2 | Consult peer; not under Advisor |
| `system-architect` | Shared multi-owner contract or ≥2 FE/API/BE/DB layers | Subagent, writes one named contract | 2 | Contract before Lead allocates; not FIO, builder, TE, or Gatekeeper |
| `backend-engineer` | Server/API/persistence | Subagent, write to owned paths | 1 build | Exclusive file ownership |
| `frontend-builder` | UI implement after UX contract | Subagent, write to owned paths | 1 build | No product/UX direction ownership |
| `frontend-ux-lead` | Journey/UX contract | Subagent | 1–2 | Contract first; implement only if brief assigns writes |
| `docs-steward` | Named durable docs | Subagent | 0 | After accepted validation when gate requires docs |
| `code-reviewer` | Independent post-integration review of an immutable candidate and v1 packet | Subagent, read-only/non-final | 1 validate | Before conditional TE routing and Gatekeeper; never accepts |
| `test-engineer` | Runtime evidence when Reviewer route requires it | Subagent | 1 validate | After Reviewer and before Gatekeeper only |
| `gatekeeper` | Final accept/block after Reviewer and TE when required | Subagent, read-only | 2 | Always final; never simultaneous with TE |
| Lead (parent) | Orchestrate only | This skill / main thread | 2 for plan; else ambient | No implementation code from Lead |

## Sequencing rules

```text
WIP ≤ 2 ordinary tool-using subagents at once; plus ≤ 1 read-only supervisor-relay subagent only when the frozen contract admits it (maximum child lanes = 3)
Debate (when required): Investigator → Advisor → Contradictor → Lead resolve → build → Code Reviewer
Reviewer verdict route and TE triggers → core/qa-operating-model.md only
Gatekeeper is always final; Reviewer never accepts or substitutes for Gatekeeper
Terminal handoff must state one recommended next to-do and Pending tasks: NONE
or a compact queue; Lead runs core/tools/validate_terminal_closeout.py before
treating it as closed
Valid DONE / COMPLETE handoff with validated closeout → next pre-admitted Batch Task
PARTIAL / failure / block / missing evidence / unowned or out-of-scope work / Gatekeeper BLOCK → stop → ask human
REVISE → named owner → corrected candidate and fresh evidence chain
```

The optional `hooks/terminal-closeout.hooks.json` template binds Codex's
`SubagentStop` event to the same validator. It checks the event working
directory for the existing `coding-team:begin` project marker, so ordinary
projects are ignored. A malformed closeout receives one continuation; a second
failure returns `BLOCKED` and cannot loop. The template is opt-in and does not
edit global or project configuration.

## Prompt packet (every spawn)

Pass only: objective, acceptance, exclusive write/read paths, evidence pointers, validation command, stop condition, mapped `model` + `effort` if the runtime supports them. The emitted prompt must identify one sole specialist, prohibit nested delegation, make unlisted paths read-only, and require `BLOCKED` when the scope is insufficient. Do not paste full files, diffs, or prior transcripts.
