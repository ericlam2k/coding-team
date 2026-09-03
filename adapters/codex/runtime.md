# Codex runtime — role delegation

Lead (this skill) classifies nature, writes a ≤250-word run prompt, and spawns
**one** Codex subagent per task. Prefer independent subagents with the planned
model/effort from the approved `model-pool.map.md`; never invent a provider slug
or silently substitute a role's model.

“Worker” is host/runtime terminology only. It is not a canonical role and must
not be used as a routing or model-map entry. A Functional Integration Owner
(FIO) is likewise a temporary overlay on one existing task owner, not a second
spawn: the Frontend Builder or Backend Engineer (or explicitly named UX owner)
performs the admitted seam check within its exclusive paths. The Lead records
the overlay in the Batch brief; no `fio` role card, skill, tier, or adapter
entry may be invented.

## Stable policy reuse and receipts

The host may inject the adapter skill on every turn, which is outside this
repository's control. The Lead resolves the stable repository policy bundle
once per matching opaque `session_id` and `context_fingerprint`, then uses the
session-local policy manifest for later `HIT` checks. `MISS`, `INVALIDATED`,
`BYPASSED`, or `UNAVAILABLE` requires a fresh policy read before a
policy-sensitive delegation; a missing session or context fingerprint fails
closed. The
manifest contains metadata/digests only. Role-card bytes remain uncached and
must pass the per-delegation preflight below.

Each check appends a local Monitor observation to
`.coding-team/runs/policy-cache-events.jsonl` with cache status, reason, named
local timing, and token-status provenance. A cache hit never implies provider
KV-cache use, token savings, cost, freshness, or authority. If the host/runtime
does not supply named token units, report `UNAVAILABLE`.

## Mandatory pre-delegation role-card check

Before delegation, Lead must:

1. resolve the selected canonical role card from a non-empty
   `CODING_TEAM_ROOT`, or from the repo-local
   `coding-team/core/roles/<canonical-id>.md` fallback;
2. read the **complete** canonical card, not a summary or guessed role;
3. run the user-invoked `role-card.check` preflight when the flow adapter is in
   use. It has read-only filesystem/card access plus an explicit metadata-only
   flow-state write (action/evidence/status); and
4. record source, sanitized path reference, SHA-256, readability/preflight
   status, baseline status, and consumption status in the local handoff.

`READABLE` plus `READABLE_AT` means only that the selected bytes were read and
hashed at a recorded preflight time. It never means host-attested consumption.
The metadata write must not mutate workflow/model-map/artifacts or invoke a
role. For ordinary Codex delegation, the current preflight plus a project-local
Task handoff is sufficient. Record task/run ID, canonical role, matching card
hash, exclusive scope, planned → actual model/effort, result, and
artifact/evidence references. When the host supplies no role-consumption event,
use `UNVERIFIED`; that absence is not a dispatch gate and must not stop
unrelated work.

Only an approved host runtime event for the same task may set `CONSUMED`. If a
receipt is supplied, its canonical role ID, card hash, task/run ID, and local
evidence must match or the handoff fails closed. The adapter never mints,
repairs, or infers a host receipt.
Missing, unreadable, invalid, stale, or baseline-blocked cards fail closed to
the human and `role-card.check`; do not auto-load, retry, spawn, or infer role
authority. Never put card contents or absolute host paths in the prompt packet,
receipt, or public-safe projection.

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
role, set `fork_context=false`; the live host cannot combine an explicit
`agent_type` with a full-history fork. `fork_context=true` and numeric
`fork_turns` are rejected rather than silently changing role or context. Never
pass a raw packet or opaque brief to `spawn_agent`. Opaque, encrypted-only,
missing, non-canonical, or out-of-scope values fail closed.

Keep candidate-wide identity checks outside a narrower worker validation
list. `MEASURED` timing units require an evidence reference. `ESTIMATED`
returns `MEASURE`; a prior hard stop returns `BLOCK`.

Run the guard from the Coding Team checkout, for example:

```bash
python3 "$CODING_TEAM_ROOT/adapters/codex/scripts/prepare-dispatch.py" \
  --input /path/to/dispatch-packet.json \
  --coding-team-root "$CODING_TEAM_ROOT"
```

Only a `READY` result may be passed to the host. Its `spawn` object uses exactly
`agent_type`, `fork_context`, `message`, `model`, and `reasoning_effort`. The
message is capped at 250 words and names the absolute
canonical role-card path with an instruction to read it first. `BLOCKED`
results have no usable spawn packet; Lead stops and corrects the brief rather
than dispatching an encrypted blob or retrying the same malformed packet.

The result also carries a deterministic `dispatch_id`. Use
`dispatch_id + agent_thread_id + call_id` as the evidence identity. Invoke the
returned `spawn` object once. Do not mirror the initial objective through
`send_message` or `followup_task`; reserve those operations for a new material
plaintext delta or a requested correction. This follows the standard
at-most-once delivery and idempotency-key pattern. Codex UI activity rows may
render one call more than once and are not authoritative run or usage counts.

This is a Codex-adapter guard, not host enforcement. A `READY` result proves
only that this adapter built a bounded plaintext request and resolved the card
path. It does not prove that a host consumed the role card, accepted the model
route, or prevent a caller from bypassing this script through another spawn
entry point. It cannot patch or alter the host collaboration API. Host/runtime
receipts remain the authority for actual model use and role-card consumption.

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

FIO status is reported by the assigned canonical task and handed to TE; it
does not authorize a model hop, cross-owner write, role reallocation, or
Gatekeeper decision. Material drift follows **FIO → Lead → System Architect**.

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

Pass only: objective, acceptance, exclusive write/read paths, evidence pointers,
validation command, stop condition, task/run ID, canonical role, card hash and
preflight/consumption status, and the mapped `model` + `effort` if the runtime
supports them. The Lead has already read the full card; do not paste card
contents, absolute paths, diffs, or prior transcripts into the prompt packet.
The project-local handoff returns to Lead or the next canonical owner. Ordinary
handoffs never route through Docs Steward.
