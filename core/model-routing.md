# Model routing (abstract tiers)

Lead classifies **task nature**, then assigns the **lowest-cost capable** tier. Tiers are **non-binding guidance**: record `planned → actual | not available` in the brief or performance log; never block start on model identity.

Host-specific model slugs live only in the install-time file `model-pool.map.md` (see adapter / docs). **This file has no host slugs.**

## One-line rule

Premium models decide. Eco models build. Cheap models search and document. Human gate controls irreversible risk. Contradictor challenges before build when required. Gatekeeper accepts only after evidence.

## Capability tiers

| Tier | Use | Capability intent |
|---|---|---|
| **0** | N0 lookup, Docs | Cheapest capable utility |
| **1 build** | N1 / post-plan implement | Eco implementer |
| **1 validate** | N3 / Test Engineer | Careful validator |
| **2** | Advisor, Contradictor, Gatekeeper, Lead plan | Premium plan / debate / review |
| **3** | N5; Adv vs Con deadlock on high risk | Max-risk judgment |

Prefer a **different model family** for Contradictor vs Advisor, and Gatekeeper vs implementer, when the pool has multiple families. On a single-family pool, differentiate with **effort + independent subagent** and record that substitution.

## Role capacity defaults (non-binding)

Map via `model-pool.map.md` after install — these are intents, not host slugs:

| Role / cell | Prefer tier | Notes |
|---|---|---|
| Investigator; low-risk Frontend Builder; eligible support cells | **0** | Cheap utility (often Luna-class on Codex) |
| Frontend Builder (complex UI); Test Engineer | **1 build** / **1 validate** | Everyday implement / careful validate |
| System Architect; Backend; Frontend/UX Lead; Docs (deep); PM; Advisor; Domain Advisor; Contradictor; Gatekeeper; Lead plan | **2** | Premium plan / debate / review |
| N5 judgment; Adv↔Con deadlock | **3** | Max-risk only |

Escalate Tier 0 → 1 when evidence conflicts, cross-module/stateful complexity, validation failure, or a11y/security/privacy/public-contract impact appears. Escalate to Tier 2/3 only under the recorded triggers below.

## Nature → route

| Nature | Delegate | Tier | Advisor | Contradictor | Gatekeeper |
|---|---|---|---|---|---|
| **N0** Map/fact | Investigator | 0 (1 if cross-file) | No | No | No (unless fact feeds N5) |
| **N1** Bounded build | Backend / Frontend Builder / TE if test-heavy | 1 build | No unless hidden risk | No unless hidden risk | **Batch** TE→GK after integrate; skip only pure N0/docs |
| **N2** Contract/UX/integration | Inv → (PM/domain if ambiguous) → System Architect for shared technical contract → Adv? → Con? → builders → TE → GK | 2 plan/critique; 1 build; 2 GK if material | Yes if direction non-obvious | **Required** if shared public contract, migration, auth/privacy, or multi-owner integration; else optional | Yes for material contract |
| **N3** Validate/classify | Investigator / TE; Adv if release-impacting | 1 validate; 2 if architecture/security/release | Only if major decision | Only if disputed | If release-impacting |
| **N4** Independent decide | Advisor; Contradictor when conflict/expensive; GK only post-implement | 2; 3 if irreversible | Yes | Yes when conflict / expensive reverse | After implement or completed packet |
| **N5** High-risk | Inv → PM? → Domain Advisor? → Adv → Con → **human gate** → eco build → TE → GK | 3 judgment; 1 build after approval | Yes | **Yes** | Yes |
| **Consult** | Product Manager **and/or** Domain Advisor (peers); optional technical Advisor | 2 medium | Optional strategic | Optional if expensive misdirection | No unless consult becomes implement |
| **Docs** | Docs Steward | 0 (1 if deep synthesis) | No | No | If docs describe public contract / compliance / security |

On Consult / N5 when specialty judgment is needed and **domain is not named**: Lead asks the human for the domain, then instantiates `{domain}-advisor` per [domain-advisors.md](domain-advisors.md). Do not default to Talent or any product-specific domain.

For triggered **N1/N2/N5** user-facing workflows, input parsing or matching, AI extraction, or public-contract work, insert a conditional pre-build Test Engineer scenario-design task after product/domain decisions and before builders. This freezes design input only; retain a fresh post-integration Test Engineer for final evidence before Gatekeeper.

## Role separation (non-negotiable)

| Role | Answers | Timing |
|---|---|---|
| **Advisor** | What should we do technically? | Before implement |
| **Contradictor** | Why might this be wrong? | Before implement |
| **Domain Advisor** | What does the named domain say? | Consult (peer to PM) |
| **Gatekeeper** | Can this be accepted as done? | After implement + evidence |
| **Product Manager** | Product scope / acceptance | Consult |
| **System Architect** | Backbone, framework, API, data, and cross-cutting technical contract | Before builders; integration owner when assigned |

## Lean concern routing

Do not convene every advisory role for each concern. Lead starts with the
single accountable role and the smallest evidence packet, then adds at most one
role at a time only when a distinct, decision-changing question remains:

1. Route product scope to Product Manager, named-domain meaning to the
   applicable Domain Advisor instance, technical direction to Advisor, and
   validation sufficiency to Test Engineer.
2. Add Contradictor only for material conflict, costly reversal, shared/public
   contracts, security/privacy, or an explicit challenge request.
3. Expand only when the current role cannot own the unresolved domain; record
   the trigger and expected decision artifact.
4. Stop once evidence is sufficient. Never call a standing brainstorm team or
   load all roles/skills by default.

This escalation remains serial and under WIP ≤2. A Domain Advisor is a peer to
Product Manager, not a replacement for it.

### Concern method router

Choose the smallest method that fits: evidence-checked `5 Whys` for a known or
recurring defect; a hypothesis tree/causal map for unclear or multi-causal root
cause; a three-option decision matrix for product choice; a stakeholder-lens
matrix for trust/fairness/consent/domain meaning; ADR trade-offs for
architecture; a time-boxed pre-mortem for release risk; and time-boxed
brainwriting with at most two relevant roles for open ideation. `5 Whys` is not
a universal default.

Each method returns: concern, evidence, hypotheses/options, affected
stakeholders, recommended decision, validation experiment, and stop/escalation
condition. Record material dissent; unresolved policy/value trade-offs go to
the human gate.

Debate for N2 (when Contradictor required), N4 (when required), N5: **serial** (Inv → Adv → Con → Lead resolve → build → TE → GK). Never three concurrent debate agents. WIP ≤ 2 still applies ([concurrency.md](concurrency.md)).

## Escalation (recorded triggers only)

- Tier 0→1: cross-file / behavior trace / edits needed
- Tier 1→2: contract, architecture, security/privacy/auth/migration/release, conflict, Advisor/Contradictor required, Tier 1 fails **twice**
- Tier 2→3: irreversible, high production/public/migration/security impact, Adv vs Con material disagreement on high risk, two serious attempts failed

**Not** escalation: first PARTIAL, context overflow (same tier, shrink packet).

## Anti-burn

- No Tier 3 for routine implementation or boilerplate
- No premium models for long mechanical edits
- Focused evidence packets; log Tier 2/3 in a performance entry
- Target mix: ~70–80% Tier 0/1, ~15–25% Tier 2, ~0–5% Tier 3

## Lead resolution (after debate)

```text
## Advisor Position
## Contradictor Position
## Lead Resolution: Proceed | Modify | Reject | More evidence
## Reason
## Final Implementation Instruction
```
