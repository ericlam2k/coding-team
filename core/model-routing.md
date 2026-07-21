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

## Nature → route

| Nature | Delegate | Tier | Advisor | Contradictor | Gatekeeper |
|---|---|---|---|---|---|
| **N0** Map/fact | Investigator | 0 (1 if cross-file) | No | No | No (unless fact feeds N5) |
| **N1** Bounded build | Backend / Frontend Builder / TE if test-heavy | 1 build | No unless hidden risk | No unless hidden risk | **Batch** TE→GK after integrate; skip only pure N0/docs |
| **N2** Contract/UX/integration | Inv → (PM if ambiguous) → Adv? → Con? → builders → TE → GK | 2 plan/critique; 1 build; 2 GK if material | Yes if direction non-obvious | **Required** if shared public contract, migration, auth/privacy, or multi-owner integration; else optional | Yes for material contract |
| **N3** Validate/classify | Investigator / TE; Adv if release-impacting | 1 validate; 2 if architecture/security/release | Only if major decision | Only if disputed | If release-impacting |
| **N4** Independent decide | Advisor; Contradictor when conflict/expensive; GK only post-implement | 2; 3 if irreversible | Yes | Yes when conflict / expensive reverse | After implement or completed packet |
| **N5** High-risk | Inv → PM? → Adv → Con → **human gate** → eco build → TE → GK | 3 judgment; 1 build after approval | Yes | **Yes** | Yes |
| **Consult** | Product Manager (peer); optional technical Advisor | 2 medium | Optional strategic | Optional if expensive misdirection | No unless consult becomes implement |
| **Docs** | Docs Steward | 0 (1 if deep synthesis) | No | No | If docs describe public contract / compliance / security |

## Role separation (non-negotiable)

| Role | Answers | Timing |
|---|---|---|
| **Advisor** | What should we do? | Before implement |
| **Contradictor** | Why might this be wrong? | Before implement |
| **Gatekeeper** | Can this be accepted as done? | After implement + evidence |
| **Product Manager** | Product scope / acceptance | Consult |

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
