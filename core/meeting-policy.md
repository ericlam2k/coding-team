# Bounded concern meeting and validation policy

Use this policy for material defects, mutation/state risks, repeated failed
validation, cross-role contract conflicts, or user/domain meaning disputes.
It is a Lead-owned decision wrapper around the existing Sprint → Batch → Task
flow, not a second router or an all-role meeting.

## Explicit new-idea brainstorm trigger

When the user asks to **brainstorm a new idea**, generate ideas, or explore a
new product direction, Lead opens a bounded discovery meeting before writing a
PRD, choosing a solution, or dispatching implementation. This is a meeting
packet, not a worker task:

- Lead frames the opportunity, target segment, desired outcome, evidence, and
  the decision that must be made; Lead remains the synthesizer and PIC chooser.
- Product Manager supplies business value and customer-impact ideas.
- `advisor` supplies the technical direction, feasibility, leverage, and scale
  view; builders do not implement during the brainstorm.
- `contradictor` supplies the explicit challenge when the user asks for
  evaluation/stress testing or when risk, ambiguity, disagreement, or reversal
  cost warrants it. The Contradictor is not a praise or rubber-stamp lane.
- `frontend-ux-lead` joins only when a UX contract can change the decision; it
  is not a generic Designer role.
- Consult serially, keep WIP ≤2, and add a named Domain Advisor only when its
  domain evidence changes the decision. Never create a standing brainstorm
  panel or a new role family.
- The packet contains the canonical-role perspectives, prioritized options
  (maximum five), assumptions/experiments, scope in/out, PIC, stop condition, and one
  recommended next user action. Use
  [`core/templates/discovery-brainstorm-meeting.md`](templates/discovery-brainstorm-meeting.md)
  when a durable packet is needed. It remains `PM_IN_PROGRESS` until the user
  confirms the handoff; `auto_action: none`.

If the brainstorm reveals a shared contract, migration/auth/privacy risk, or
two or more FE/API/BE/DB layers, Lead conditionally routes to System Architect
after PM confirmation. Brainstorm output never allocates builders, invokes a
model, advances a stage, or approves a product decision on the user's behalf.

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
human gate. “Test all” means all required scenarios and selected layers in the
frozen Batch, not the whole repository or every possible layer on every loop.

At Batch or Sprint close, send material observations through
[learning-and-distillation.md](learning-and-distillation.md). Correlation is
input to learning; it is not permission to promote a new rule. A single
observation remains a candidate, and durable promotion follows the separate
validation and human-gate requirements.

The active Normal/Risky QA selection and evidence gates are in
[qa-operating-model.md](qa-operating-model.md). Gatekeeper evidence is not
production/release approval; human gates still apply.

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
