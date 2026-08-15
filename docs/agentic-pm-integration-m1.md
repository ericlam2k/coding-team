# M1 — Agentic PM Integration Evaluation

## Identity

- **Experiment ID:** `EXP-20260806-APPDEV-01`
- **Scope:** Coding Team app-development assistant only
- **State:** `OPENED`
- **Owner / PIC:** Lead
- **Opened:** 2026-08-06
- **Review point:** After 9 controlled runs, or immediately after a critical failure
- **Human decision:** pending

This milestone does **not** change the WYSY platform, WYSY product behavior,
the core Coding Team policy, the canonical role model, or the approved model
map. It evaluates a Lead-level Agentic Coding orchestrator plus one labelled PM
extension.

## Hypothesis

For app-development assistance, a Lead-level `agentic-coding-orchestrator`
combined with the labelled PM `intended-vs-implemented` method will improve
evidence quality and decision routing over either WYSY core alone or the PM
method alone, without increasing false positives, unauthorized decisions, or
review/rework burden.

## Baseline and arms

Run the same fixture, prompt, repository revision, tool access, model family,
and time budget in three arms, with three repetitions per arm:

| Arm | Skills |
|---|---|
| A — Core | WYSY Coding Team core only |
| B — PM | `intended-vs-implemented` only, labelled external |
| C — Combined | WYSY core + Lead orchestrator + labelled PM method |

The role/model map remains unchanged. Planned routing is recorded per handoff:
PM/Advisor/Contradictor/Gatekeeper use the approved Tier 2 mapping; Test
Engineer uses the approved Codex Tier 1 validate mapping. Actual model/effort
must come from the host receipt; otherwise record `unavailable`.

## Success measures

The combined arm may propose `SUCCESSFUL` only when all conditions hold:

1. Detects every seeded material defect in all three combined repetitions.
2. Has zero critical failures: fabricated evidence, lost provenance,
   unauthorized one-way-door decision, weakened check, or missed required
   human escalation.
3. Has no worse false-positive rate than both baselines.
4. Improves at least one non-text signal against both baselines:
   evidence completeness, escalation correctness, review time, or rework.
5. Produces valid same-task role-consumption receipts for any claim of
   canonical PM, Advisor, Contradictor, Test Engineer, or Gatekeeper execution.

The existing 0–2 dimensions may remain as a diagnostic vector. They are not a
probability, productivity claim, or standalone adoption decision.

## Required measurements

| Measure | Definition |
|---|---|
| Material defect detection | Seeded material defects found / seeded material defects |
| False-positive rate | Non-material findings / all findings |
| Evidence completeness | Material findings with both intent and implementation evidence / material findings |
| Unauthorized decision rate | Unauthorized one-way-door decisions / decisions |
| Provenance violations | External outputs missing required provenance / external outputs |
| Escalation correctness | Required escalations correctly routed / required escalations |
| Repeatability | Successful repetitions / total repetitions |
| Review time | Human minutes from report receipt to decision; unavailable if not measured |
| Rework | Correction cycles before an accepted evidence packet |
| Receipt completeness | Canonical role handoffs with valid receipts / claimed canonical role handoffs |
| Telemetry coverage | Runs with named model/token/cost receipts / total runs |

Report medians, ranges, denominators, and hard failures. Do not convert
unavailable telemetry into zero.

## Adaptive rules

| Observation | Action | State |
|---|---|---|
| Any critical failure in Arm C | Disable the combined adapter for app-dev assistance; open one corrective task; return to Arm A | `REVERTED` proposal |
| Arm C misses a seeded defect | Inspect the owning method; do not tune for wording; retest the smallest changed adapter | `CONTINUE` or `REVERTED` proposal |
| Arm C adds text but no measurable uplift | Keep the adapter unchanged; revise or narrow the output contract | `CONTINUE` |
| Arm C improves quality but telemetry is unavailable | Preserve quality result; make no cost/productivity claim; collect named receipts | `CONTINUE` |
| Arm C passes all success measures | Prepare a scoped adapter addendum for human approval; do not auto-promote | `SUCCESSFUL` proposal |
| Independent result contradicts the lesson | Mark the candidate contradicted and retest; do not silently edit the rule | `RETEST` |

## Stop / revert criteria

Stop the milestone and ask the human when:

- a role/model receipt is missing for a claimed canonical handoff;
- the fixture, prompt, model, or tool access changes between comparable runs;
- a report hides unavailable evidence or presents proposed tests as passing;
- the combined arm changes core routing, role definitions, model map, or WYSY
  platform behavior; or
- a critical failure repeats in two consecutive combined repetitions.

## Out of scope

- WYSY platform UI, product workflow, or platform policy;
- automatic PM marketplace installation or external skill loader;
- core role/model policy changes;
- new roles, FIO routes, or second orchestration runtimes;
- production code changes, deployments, or public claims;
- training, retraining, or automatic policy promotion.

## Evidence and decision

- **Planned → actual model/effort:** record per handoff; actual remains
  `unavailable` without a host receipt.
- **Fallback mode:** `READ_ONLY` when telemetry or role consumption is missing;
  never claim full execution.
- **Evidence refs:** run trace, scenario result, TE evidence, Gatekeeper
  decision, performance log, and role-consumption receipts.
- **Proposal:** `continue` with three-arm, three-repetition evaluation.
- **Human decision:** `pending`.
- **Promotion destination:** app-development-assistant adapter only, after
  fresh TE evidence, sequential Gatekeeper review, and explicit human approval.
