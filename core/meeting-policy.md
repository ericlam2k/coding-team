# Bounded concern meeting and validation policy

Use this policy for material defects, mutation/state risks, repeated failed
validation, cross-role contract conflicts, or user/domain meaning disputes.
It is a Lead-owned decision wrapper around the existing Sprint → Batch → Task
flow, not a second router or an all-role meeting.

## Lean participation

- **Lead:** frames the concern, runs the synthesis, chooses the PIC, and admits
  the next batch.
- **Test Engineer:** owns the scenario matrix and independent evidence.
- **System Architect:** joins for shared contracts, state, mutation,
  idempotency, currentness, or cross-module root cause.
- **Product Manager + named Domain Advisor:** join when user outcome, domain
  workflow, customary handling, fairness, or recovery meaning can change the
  decision.
- **Contradictor:** add only for material disagreement, high risk, costly
  reversal, or an explicit challenge.

Consult serially. Keep WIP ≤2, preserve disjoint write scopes, and never run a
standing brainstorm panel.

## Pre-build acceptance chain

1. PM uses `user-stories` when the user outcome or acceptance is unclear.
2. PM uses `pre-mortem` when the change has material failure, replay, stale
   state, or fix–trial-loop risk. These PM skills are sequential and
   conditional, not an automatic pair.
3. The Domain Advisor supplies named-domain cases and evidence when triggered;
   it does not approve the implementation.
4. Test Engineer uses `pm-execution/test-scenarios` to turn the accepted inputs
   into a user-observable Given/When/Then matrix, including negative and edge
   cases, and freezes it before builders start.
5. Builders write the named red unit/contract/component cases first where
   practical, then implement the smallest green boundary.

The pre-build matrix is design input, not execution evidence.

## PDCA error-correlation loop

**Plan:** Lead records concern, evidence boundary, risk, PIC, acceptance
artifact, stop condition, and clean-fixture strategy.

**Do:** builders implement one admitted corrective Batch. No product fixes are
  dispatched while the active validation pass is running.

**Check:** a fresh Test Engineer executes the complete frozen Batch matrix,
  targeted regressions, and relevant negative/adversarial cases. Log every
  finding with scenario, expected/actual result, repro, layer, evidence, and
  classification (`PRODUCT_DEFECT`, `TEST_CONTRACT_DEFECT`, `ENVIRONMENT_DEFECT`,
  `TOOL_TRANSPORT_DEFECT`, or `UNKNOWN`).

**Act:** after the pass, correlate all findings once. Cluster only by
  demonstrated shared cause, trace to the owning defect or architecture seam,
  summarize bounded hypotheses, and route to one PIC by default. Use multiple
  PICs only for distinct technical and domain decisions. Lead admits one
  integrable corrective Batch or queues a separate provisional Batch.

Run a fresh TE pass after correction, then one sequential Gatekeeper review.
`FAIL`, `BLOCKED`, insufficient evidence, or a non-approval stops for the
human gate. “Test all” means all scenarios in the frozen Batch, not the whole
repository on every loop.

## Meeting packet

```text
Concern and affected journey/contract
Verified evidence and missing evidence
User/domain signal (when triggered)
Technical risk and shared invariant
All observed findings and correlation map
Hypotheses/options (maximum three)
PIC, decision, corrective Batch, acceptance artifact, stop condition
```
