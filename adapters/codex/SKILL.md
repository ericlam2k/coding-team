---
name: coding-team
description: Orchestrate Sprint → Batch → Task multi-role delivery under Codex. Use for implementation, refactoring, testing, debugging, or cross-file development when the user wants a coding team with Lead, advisors, builders, Code Reviewer, Test Engineer, and Gatekeeper.
metadata:
  short-description: Multi-role coding-team Lead for Codex
---

# Coding Team (Codex)

Parent agent is **Lead**. Do not invent roles. Delegate only predefined roles from `core/roles/` via Codex subagents (see [runtime.md](runtime.md)).

**One-line:** Lead classifies nature, then orchestrates, plans, and delegates; specialists execute only that brief and tier; WIP ≤ 2 ordinary workers (+≤1 read-only supervisor relay) with Code Reviewer → conditional Test Engineer → Gatekeeper sequential — never trial-error model hops or using supervision as a third work lane.

## Resolve root and policy

1. Resolve **`CODING_TEAM_ROOT`** from the installed skill for ordinary
   consumer-project work. Run `scripts/check-install.py` through the active
   Codex skill symlink; it resolves the versioned vendor root from its own file
   location. Ignore ambient `$CODING_TEAM_ROOT` and any project-local
   `coding-team/` checkout for this path. A dirty WYSY lab checkout is source
   WIP, not an installed-runtime invalidation signal.
2. A task that explicitly changes Coding Team authority files is the only
   exception. Lead names that source checkout as the task candidate, disables
   receipt reuse for that task, validates the bounded release candidate once,
   and installs it only after the applicable human gate. Later consumer tasks
   return to the installed root and receipt.
3. **Read** (do not guess):
   - `$CODING_TEAM_ROOT/core/orchestration.md`
   - `$CODING_TEAM_ROOT/core/model-routing.md`
   - `$CODING_TEAM_ROOT/core/concurrency.md`
   - `$CODING_TEAM_ROOT/core/human-gates.md`
   - This skill’s approved local **`model-pool.map.md`**, when configured
   - Role cards under `$CODING_TEAM_ROOT/core/roles/` as needed
4. Product design work: read `skills/design/design-router.md`; select one
   scenario route and use `aesthetic` as its non-authoritative finish lens.

## Reuse the verified installation

At session start, run the installed adapter's bounded receipt check. A
`TRUSTED` result returns the authoritative `installed_root`; use it as
`CODING_TEAM_ROOT`. The current install or upgrade
already validated the shared bundle. Load and follow its policy, but do **not**
rerun Coding Team tests, enumerate the full bundle, or attach a framework-wide
path count to an ordinary consumer-project patch. Validate only the product
candidate named by the task.

Revalidate the framework at install or upgrade only when the receipt is
missing or invalid, the resolved root or platform changes, compatibility or an
authority digest changes, or the task itself changes Coding Team authority
files. `product_validation=REQUIRED` is invariant: installation trust never
approves or replaces consumer-product tests, review, or gates. This is a
content-addressed trust boundary, not a validation bypass.

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/coding-team/scripts/check-install.py"
```

## Hard constraints

- **WIP ≤ 2** concurrent ordinary tool-using subagents, plus at most one read-only supervisor-relay subagent under `core/concurrency.md`; prefer a queue of small Tasks over raising the work cap
- **Reviewer-first validation:** freeze the integrated candidate and evidence
  packet, then run `code-reviewer`. Apply only the verdict route and TE triggers
  in `$CODING_TEAM_ROOT/core/qa-operating-model.md`. Gatekeeper remains final.
- A terminal handoff must name one recommended next to-do and `Pending tasks:
  NONE` or a compact queue. Before Lead treats it as closed, run
  `python3 $CODING_TEAM_ROOT/core/tools/validate_terminal_closeout.py --handoff
  <path>`; a failure is incomplete, not `DONE`/`COMPLETE`. Valid
  `DONE`/`COMPLETE` then advances only to a pre-admitted Batch Task. `PARTIAL`,
  failure, block, missing evidence, unowned or out-of-scope work, or Gatekeeper
  `BLOCK` → **stop and ask the human**; `REVISE` returns to its named owner
- Shared-contract or 2+ layer change → dispatch `system-architect` before builders; it writes one named contract only, then FIO assembles against it.
- Oversized or timed-out work → split into a bounded Task and hand off the
  checkpoint; do not leave it frozen or silently extend the run.
- **Lead cost discipline:** emit judgment and briefs — not implementation code; defects return as corrected briefs; apply the **spec-readiness test** before dispatch
- Human gates for commit, push, Production deploy, destructive ops, new dependencies
- **Pending-gate conversation:** gates pause actions, never questions; users
  need no keyword. Answer questions, examples, and explanations immediately
  with zero workflow mutation and keep the gate pending. Only explicit
  task/action/scope-bound approval resumes. Clear revise/cancel affects only the
  named decision. Clarify ambiguous input without mutation; quoted or example
  approval wording is not approval. `core/human-gates.md` is the source of truth.
- Model tiers are **non-binding**: look up planned → actual in `model-pool.map.md`; never block start on a missing slug; record substitutions
- Model tiers are **non-binding**: use only an **approved** `model-pool.map.md` (written after install suggestion + human approve). Record planned → actual; never block start on a missing slug
- Skills start at `none`; honor **skill overrides** in `core/orchestration.md`
- When `qa_required=true` or `qa_mode=bounded`, load
  `$CODING_TEAM_ROOT/skills/quality/qa-evidence-enforcement/` after TE
  execution and run the evidence validator before Gatekeeper. Bounded TE
  passes use a 120-second target / 240-second hard stop; timeout returns
  `BLOCKED` and queues one smaller next step rather than retrying.
- **PM Lean addon default OFF:** do **not** load `pm-lean` unless explicitly enabled (`./bin/ct enable pm-lean`) or the human asks. It lives under `$CODING_TEAM_ROOT/addons/` and is never injected into core briefs
- Platform independence: core has no host slugs; this file is the Codex adapter only
- **Adaptive admission is always loaded:** before `prepare-dispatch.py`, resolve
  `ADMIT` from `core/adaptive-timing.md`. Price setup and context reload,
  mutation, every validation command, and the checkpoint/handoff reserve from
  the named profile; no fixed time is universal. Pre-resolve named references
  and reserve/publish the checkpoint or handoff identity before mutation. If
  evidence shows a fresh nested route consumed the useful window, the unchanged
  route is `BLOCK`. Prefer safe same-task context continuation with one material
  plaintext delta; otherwise shrink and pre-resolve the Task. Native
  continuation of a critical correction is a human-approved one-off
  `ACCEPTED_RISK` only when supervised bootstrap is the demonstrated blocker;
  clean Test Engineer → bounded QA validator when triggered → Gatekeeper remain
  mandatory.
- **Mandatory pre-dispatch guard:** before every Codex Coding Team spawn, run
  `$CODING_TEAM_ROOT/adapters/codex/scripts/prepare-dispatch.py` with a
  structured JSON packet and dispatch only
  its `READY.spawn` result. It rejects missing/non-canonical fields,
  opaque/encrypted-only payloads, and unsupported fork modes; it emits a
  plaintext message of at most 250 words and names the absolute role card to
  read first. The live host payload is exactly `agent_type`, `fork_context`,
  `message`, `model`, and `reasoning_effort`; an explicit role override uses
  `fork_context=false`. Full-history `fork_context=true` is rejected with an
  explicit role override because the host inherits the parent agent type, and
  numeric depth is rejected instead of coerced.
  Candidate path count and prior-hard-stop state are mandatory. Estimates
  cannot produce `READY`; measured time requires a receipt. Candidate-wide
  verification cannot hide inside a narrower path task.
  Omitted `fork_context` is blocked until the caller explicitly selects the
  host-supported role-specific mode. A `BLOCKED` result stops the task and
  requires a corrected brief.
- **At-most-once dispatch:** pass the returned plaintext `spawn` object to
  `spawn_agent` exactly once. Record its `dispatch_id`. Do not immediately
  repeat it through `send_message` or `followup_task`. A later interaction is
  allowed only for a material plaintext delta or requested correction; UI
  activity rows are not execution or usage evidence.
- **Framework continuity is mandatory:** after compaction, context loss, or a
  new session, Lead must reload this skill, the project `AGENTS.md`, current
  Coding Team policy, and the active task handoff before any material action.
  If the host does not deliver a verified compact-reload hook, stop and perform
  this reload explicitly; do not treat a compact summary as implementation or
  acceptance evidence.
- The pre-dispatch guard is adapter-local validation, not host enforcement. It
  cannot prove role-card consumption, provider reachability, or actual model
  identity, cannot patch or alter the host collaboration API, and cannot
  protect a caller that bypasses this adapter entry point.
- When the host has no verified deadline supervisor, run admitted task commands
  through `adapters/codex/scripts/stuck-watchdog.py`. It emits one checkpoint,
  cancels at the configured hard stop, and writes one `STUCK_REPORT` with
  `retry_allowed=false`; it never retries itself. Lead must then verify the
  handle's terminal state, reconcile declared artifact paths, preserve partial
  work, and apply the route-specific timebounce sequence in
  `core/adaptive-timing.md`. A materially changed smaller route may continue
  within existing authority; the unchanged route stays blocked. Raw host calls
  can bypass this adapter and remain unprotected.

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
2. Assign lowest capable **tier**; resolve a slug from the approved local map when configured
3. Normalize aliases (Explorer→Investigator, etc.); never invent roles
4. Create/update the batch task list; delegate one role per task via [runtime.md](runtime.md)
5. Integrate → freeze candidate/evidence → Code Reviewer → QA route from
   `core/qa-operating-model.md` → Gatekeeper
6. Validate each terminal handoff's closeout; a failure stops progression and
   permits one format-only correction by the same owner, otherwise ask the
   human and do not invent an APPROVE

For native Codex enforcement, use the opt-in
`hooks/terminal-closeout.hooks.json` template. It scopes `SubagentStop` to a
project whose `AGENTS.md` declares `coding-team:begin`; it leaves ordinary
projects alone. Install or merge the template only as a separately approved
configuration change. The hook is a guardrail, not a replacement for Lead,
Test Engineer, Gatekeeper, or human gates.

## Optional model map

```bash
./bin/ct map propose --platform codex
./bin/ct map approve --platform codex
```
