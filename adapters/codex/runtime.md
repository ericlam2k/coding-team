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

## Delegation table

| Canonical role | When to spawn | Codex pattern | Tier (look up map) | Notes |
|---|---|---|---|---|
| `investigator` | N0 map/fact; N2/N5 pre-scan | Subagent, read-mostly | 0 (1 if cross-file) | Path/line evidence only; no edits |
| `advisor` | N2/N4/N5 direction | Subagent, read-only | 2 | Pre-build verdict; never implements or Gatekeeps |
| `contradictor` | Required N2/N4/N5 debate | Subagent, read-only | 2 | **Serial after Advisor**; never parallel with Advisor under WIP |
| `product-manager` | Ambiguous product scope | Subagent | 2 | Consult peer; not under Advisor |
| `system-architect` | Shared multi-owner contract or ≥2 FE/API/BE/DB layers | Subagent, writes one named contract | 2 | Contract before Lead allocates; not FIO, builder, TE, or Gatekeeper |
| `backend-engineer` | Server/API/persistence | Subagent, write to owned paths | 1 build | Exclusive file ownership |
| `frontend-builder` | UI implement after UX contract | Subagent, write to owned paths | 1 build | No product/UX direction ownership |
| `frontend-ux-lead` | Journey/UX contract | Subagent | 1–2 | Contract first; implement only if brief assigns writes |
| `docs-steward` | Named durable docs | Subagent | 0 | Named path + fresh TE PASS + sequential GK APPROVE/APPROVE_WITH_NOTES |
| `test-engineer` | Batch V0–V3 evidence | Subagent | 1 validate | Before Gatekeeper only |
| `gatekeeper` | Post-TE accept/block | Subagent, read-only | 2 | **After** fresh TE evidence; never with TE |
| Lead (parent) | Orchestrate only | This skill / main thread | 2 for plan; else ambient | No implementation code from Lead |

FIO status is reported by the assigned canonical task and handed to TE; it
does not authorize a model hop, cross-owner write, role reallocation, or
Gatekeeper decision. Material drift follows **FIO → Lead → System Architect**.

## Sequencing rules

```text
WIP ≤ 2 tool-using subagents at once
Debate (when required): Investigator → Advisor → Contradictor → Lead resolve → build → TE → GK
Validation gate: Test Engineer completes → then Gatekeeper
Incomplete / non-APPROVE → stop → ask human
```

## Prompt packet (every spawn)

Pass only: objective, acceptance, exclusive write/read paths, evidence pointers,
validation command, stop condition, task/run ID, canonical role, card hash and
preflight/consumption status, and the mapped `model` + `effort` if the runtime
supports them. The Lead has already read the full card; do not paste card
contents, absolute paths, diffs, or prior transcripts into the prompt packet.
The project-local handoff returns to Lead or the next canonical owner. Ordinary
handoffs never route through Docs Steward.
