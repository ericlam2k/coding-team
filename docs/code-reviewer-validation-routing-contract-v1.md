# Code-reviewer validation and routing contract v1

> Host-neutral shared contract. It defines the minimum quality-chain
> invariants; it does not allocate work, implement routing, or accept changes.

## Identity

- **Contract ID / status / freeze date:** WYSY-CODE-REVIEWER-VALIDATION-ROUTING-v1 / `AMENDED_FOR_LEAN_IMPLEMENTATION` / 2026-08-25
- **Trigger:** shared validation contract across workflow, evidence, roles, and adapters
- **System Architect planned → actual / downshift:** Tier 2 → Tier 2 / none recorded
- **Lead / FIO:** Lead allocates owners and names the FIO after this freeze

## Scope

- **Outcome:** `Builder → deterministic checks → Code Reviewer → conditional Test Engineer → Gatekeeper`.
- **Source of truth:** [`core/qa-operating-model.md`](../core/qa-operating-model.md) alone defines TE triggers, direct-route eligibility, and Reviewer-verdict routes. Other files link to it instead of repeating those rules. This applies DRY / single-source-of-truth.
- **Out of scope:** implementation state machines, packet-version negotiation, a separate direct-route enablement state, correction/task-progression policy, host model selection, retries, acceptance, commit, external enablement, push, or release. This applies YAGNI to dormant machinery.

## Contract

| Area | Decision / invariant | Owner after allocation | Evidence label |
|---|---|---|---|
| Candidate and artifact | Freeze one candidate key: commit/tree plus dirty-state digest when needed. The review artifact contains that key, reviewed scope, findings, verdict, selected route, residual risk, and evidence references. Any mutation invalidates Reviewer and TE evidence. | Builder/FIO freezes; evidence owner binds | reasoned-not-tested |
| Reviewer boundary | `code-reviewer` is independent of the candidate author, read-only, diff-first, and non-terminal. It cannot mutate, allocate, spawn, test broadly, or accept. This preserves NIST SP 800-53 AC-5 separation of duties. | Code Reviewer | reasoned-not-tested |
| Deterministic evidence | Run the smallest relevant declared checks before review and reference their exact results. Missing, failed, mismatched, or insufficient evidence never permits a direct Gatekeeper route. | Builder/FIO | reasoned-not-tested |
| Runtime evidence | TE executes only the bounded runtime, behavioral, integration, regression, or release-risk scope required by the QA source of truth. It does not repeat broad static review. | Test Engineer | reasoned-not-tested |
| Routing and failure | Lead applies only the canonical route from the QA source of truth. Unknown verdicts, uncertain triggers, unresolved `BLOCKER` findings, identity mismatch, stale evidence, or ambiguous legacy values fail closed and cannot reach Gatekeeper. | Lead / adapter | reasoned-not-tested |
| Compatibility | Core accepts canonical role IDs, verdicts, and routes only. A supported adapter may translate known legacy values at its boundary, must preserve meaning, and must reject unmapped values. No legacy branch or host-specific model slug enters core policy. | Adapter owner | reasoned-not-tested |
| Final decision | Gatekeeper receives the immutable candidate, deterministic results, Reviewer artifact, TE evidence when required or the QA-defined direct-route rationale, residual risk, and human decisions. Gatekeeper alone accepts, revises, or blocks; unresolved `BLOCKER` findings forbid acceptance. | Gatekeeper | reasoned-not-tested |

## Options and decision

- **Options:** require TE for every candidate; add a product-owned routing state machine; or use one canonical review artifact plus risk-triggered TE.
- **Decision:** use the third option. It preserves execution evidence where static review is insufficient while removing duplicated policy and dormant orchestration.
- **Cost / reversibility / residual risk:** adapters need bounded compatibility tests. Revert by routing all candidates through TE. Residual risk is incorrect trigger classification; fail-closed uncertainty and Gatekeeper challenge limit it.
- **Cheapest validation:** fixtures for the low-risk direct route, every QA TE trigger, mutation invalidation, Reviewer non-acceptance, known legacy translation, unknown-value rejection, and Gatekeeper finality.

## Allocation constraints

- One writer per file; tool-using WIP ≤2.
- Sequence one candidate: mutating builders stop → freeze/checks → Reviewer → TE when routed → Gatekeeper. These roles do not overlap for that candidate.
- Existing irreversible human gates in [`core/human-gates.md`](../core/human-gates.md) remain unchanged. This contract creates no micro-gate.
- Material contract drift returns **FIO → Lead → System Architect**.

## Acceptance boundary

- [x] Candidate identity, ownership, failure behavior, compatibility boundary, and evidence chain are frozen.
- [x] `qa-operating-model.md` is the sole TE-trigger and route source.
- [x] No dormant route-enable subsystem, correction subsystem, host slug, implementation approval, or acceptance decision is introduced.
