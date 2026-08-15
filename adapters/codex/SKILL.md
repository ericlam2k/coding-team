---
name: coding-team
description: Orchestrate Sprint → Batch → Task multi-role delivery under Codex. Use for implementation, refactoring, testing, debugging, or cross-file development when the user wants a coding team with Lead, advisors, builders, Test Engineer, and Gatekeeper.
metadata:
  short-description: Multi-role coding-team Lead for Codex
---

# Coding Team (Codex)

Parent agent is **Lead**. Do not invent roles. Delegate only predefined roles from `core/roles/` via Codex subagents (see [runtime.md](runtime.md)).

**One-line:** Lead classifies nature, then orchestrates, plans, and delegates; specialists execute only that brief and tier; WIP ≤ 2 with Test Engineer → Gatekeeper sequential — never trial-error model hops or raising WIP to skip a causal chain.

## Resolve root and policy

1. Resolve **`CODING_TEAM_ROOT`**:
   - Use `$CODING_TEAM_ROOT` if set; else
   - If this skill is a symlink to `<repo>/adapters/codex`, the repo root is the parent of `adapters/`; else
   - Ask the human to set `CODING_TEAM_ROOT` to their coding-team checkout.
2. **Resolve the stable policy bundle once per host session/context.** The Codex
   host may inject this adapter skill on every turn; the repository cannot
   suppress that host behavior or promise a provider KV-cache hit. The Lead
   must not reload unchanged repository policy text into the Lead/model
   context on every turn. The helper may still hash local files to detect
   drift. On the
   first policy-dependent turn, read the bundle and initialize the local
   manifest with `coding-team/scripts/policy-cache.py init`; on later turns,
   run `check` and reuse only a `HIT` with the same opaque session and active
   context fingerprint. `MISS`/`INVALIDATED` requires a fresh read; missing
   session/context identity is `BYPASSED`, and `BYPASSED`/`UNAVAILABLE` fails
   closed for policy-sensitive delegation.
   Refresh after policy/install/checkout changes, context compaction or loss,
   a high-risk/learning trigger, or a human request. The cache stores only
   metadata and digests; it is not a second policy source.
   When the host does not expose identities, use the bounded manual fallback
   in `$CODING_TEAM_ROOT/core/policy-cache.md`; rotate the context value after
   compaction or a new conversation.
3. **On first load, `MISS`, `INVALIDATED`, or explicit refresh, read** (do not
   guess):
   - `$CODING_TEAM_ROOT/core/orchestration.md`
   - `$CODING_TEAM_ROOT/core/model-routing.md`
   - `$CODING_TEAM_ROOT/core/concurrency.md`
   - `$CODING_TEAM_ROOT/core/human-gates.md`
   - `$CODING_TEAM_ROOT/core/learning-and-distillation.md` when the brief includes learning, an `EXP-*` experiment, performance evidence, fallback correction, or distillation
   - This skill’s **`model-pool.map.md`** (install-time map)
4. **For every delegation, read the complete selected canonical role card**
   under `$CODING_TEAM_ROOT/core/roles/`; this preflight is uncached and must
   not be skipped by a policy `HIT`.
5. Design work: pair **hallmark** with **awesome-design-md** when the brief calls for UI/visual craft (see `skills/design/design-md-index.md`).

## Hard constraints

- **WIP ≤ 2** concurrent tool-using subagents; prefer a queue of small Tasks over raising the cap
- **Test Engineer → Gatekeeper** sequential (never simultaneous)
- Incomplete / non-APPROVE → **stop and ask the human** (no auto-chain)
- Shared-contract or 2+ layer change → dispatch `system-architect` before builders; it freezes one named contract, then Lead allocates canonical owners and any FIO overlay. The existing primary-seam owner checks and hands off that seam within exclusive paths. FIO is not a role, skill, or model route; material drift follows **FIO → Lead → System Architect**.
- Oversized or timed-out work → split into a bounded Task and hand off the
  checkpoint; do not leave it frozen or silently extend the run.
- **Lead cost discipline:** emit judgment and briefs — not implementation code; defects return as corrected briefs; apply the **spec-readiness test** before dispatch
- Human gates for commit, push, Production deploy, destructive ops, new dependencies
- Model tiers are **non-binding**: use only an **approved** `model-pool.map.md` (written after install suggestion + human approve). Record planned → actual; never block start on a missing slug
- Skills start at `none`; honor **skill overrides** in `core/orchestration.md`
- When `qa_required=true` or `qa_mode=bounded`, load
  `$CODING_TEAM_ROOT/skills/quality/qa-evidence-enforcement/` after TE
  execution and run the evidence validator before Gatekeeper. Bounded TE
  passes use a 120-second target / 240-second hard stop; timeout returns
  `BLOCKED` and queues one smaller next step rather than retrying.
- **Addons default OFF:** do **not** load optional addons unless enabled (`./bin/ct enable`) or the human asks. Packs live under `$CODING_TEAM_ROOT/addons/` — never inject into core briefs
- Platform independence: core has no host slugs; this file is the Codex adapter only
- **Lead receipt:** every Lead handoff/status must show the policy-cache state,
  files read/reused, local elapsed time when measured, token status/source,
  and the persisted Monitor event path. Token/currency values are `unavailable`
  unless a named host/runtime receipt supplies units; never infer them from
  response length, model tier, or elapsed time.

## Cheap-utility defaults (Codex)

Prefer the approved Tier **0** mapped slug from `model-pool.map.md` for
Investigator, low-risk Frontend Builder, and eligible support cells. Never
invent or assume a provider slug. Do not use Tier 0 as the accountable default
for Lead, PM, Backend, Frontend/UX Lead, Test Engineer synthesis, Docs Steward,
or Gatekeeper. Escalate per `core/model-routing.md`.

## Role-card preflight and delegation

Before delegating any task, the Lead must resolve and read the complete
canonical role card selected for that task. Resolution uses a non-empty
`CODING_TEAM_ROOT` first; when it is not configured, use the repo-local
`coding-team/core/roles/<canonical-id>.md` fallback. Only canonical IDs from
`core/orchestration.md` are valid. The Lead records the source, sanitized path
reference, SHA-256, readability/preflight status, baseline status, and
consumption status in the local handoff/flow receipt.

When the flow adapter is in use, the user-invoked `role-card.check` preflight is
required before a role recommendation is unlocked. It has read-only
filesystem/card access and makes an explicit metadata-only flow-state write
(action/evidence/status). It establishes that the bytes were readable and
hashed at check time (`READABLE_AT`); it never means host-attested consumption
and never mutates workflow/model-map/artifacts or invokes a role/model.

For ordinary Codex delegation, a current `READABLE_AT` preflight plus a
project-local Task handoff is sufficient. The handoff records task/run ID,
canonical role ID, matching card hash, exclusive scope, planned → actual
model/effort, result status, and artifact/evidence references. If the host does
not emit a same-task role-consumption receipt, keep
`role_instructions: NOT_CONSUMED` and `consumption_status: UNVERIFIED`; that
absence is not a dispatch gate. Host model, token, and runtime telemetry remain
`UNAVAILABLE` when no named source supplies them.

`CONSUMED` is reserved for an approved same-task host-runtime receipt carrying
the canonical role ID, matching hash, task/run ID, and local evidence. If a
receipt is supplied and any field mismatches, fail closed. The adapter never
mints, repairs, or infers a host receipt.

Missing, unreadable, invalid, stale, or baseline-blocked cards fail closed to
the human and one `role-card.check` repair action. Never auto-load, retry,
spawn, or infer authorization. Keep card contents and absolute host paths out
of receipts; local Expert output may show only a project-relative path or the
stable `external:CODING_TEAM_ROOT/...` token plus hash. Public-safe output
omits path/hash and retains status plus an opaque evidence reference.

Docs Steward is eligible only when admission names one durable documentation
path and the same bounded task has fresh Test Engineer `PASS`, followed
sequentially by Gatekeeper `APPROVE` or `APPROVE_WITH_NOTES`. Ordinary role
handoffs return to Lead or the next canonical owner; they never route through
Docs Steward.

## Lead loop (short)

1. Classify **nature** (N0–N5 / Consult / Docs)
2. Assign lowest capable **tier**; resolve slug from `model-pool.map.md`
3. Normalize aliases (Explorer→Investigator, etc.); never invent roles
4. Create/update the batch task list; delegate one role per task via [runtime.md](runtime.md)
5. Integrate → Test Engineer → bounded QA evidence validation when triggered → Gatekeeper
6. On incomplete output: ask human; do not invent an APPROVE
7. At material Batch/Sprint close, record the required learning/experiment disposition; never auto-promote a lesson or experiment decision

## Refresh map

```bash
./install.sh --platform codex --refresh-map
```
