# Workflow (Sprint → Batch → Task)

## Flow

```text
Human goal
  → Lead classifies natures + proposes Sprint
  → Admit Batch READY (freeze validation + ownership)
  → PM/domain decisions → TE scenario matrix
  → Delegate Tasks (WIP ≤ 2)
  → Integrate → complete TE pass → correlate → one corrective Batch if needed
  → fresh Test Engineer → Gatekeeper
  → Checkpoint / next Batch or Sprint close
```

Incomplete or non-`APPROVE` output → **stop and ask the human**. Do not auto-chain.

Lead applies **cost discipline** and the **spec-readiness test** before dispatch ([orchestration.md](../core/orchestration.md)).

## Sprint

One measurable outcome, governing specs, non-goals, gates, ordered batches. Template: [`core/templates/sprint-brief.md`](../core/templates/sprint-brief.md). Cap: **600 words**.

## Batch

Dependency-safe integration + review unit. Admit `READY` only when contracts, ownership, acceptance, and blocking validation commands are clear. Template: [`core/templates/batch-brief.md`](../core/templates/batch-brief.md). Cap: **450 words**.

Default: one `ACTIVE` implementation batch and one next `READY` batch.

## Task

One owner, exclusive files, stop condition, skill = `none` or one primary. Project a ≤**250**-word run prompt — never paste the full template or whole files; send paths + line ranges.

Template: [`core/templates/task-brief.md`](../core/templates/task-brief.md).

## Review chain

1. Owner self-check
2. Fresh **Test Engineer** validation (evidence)
3. Independent **Gatekeeper** decision

TE and Gatekeeper stay **sequential** for the same batch ([concurrency.md](../core/concurrency.md)).

## Debate (when required)

`Investigator → Advisor → Contradictor → Lead resolve → eco build → TE → GK`

Lead resolution format lives in [`core/model-routing.md`](../core/model-routing.md).

## Context discipline

| Artifact | Cap |
|---|---|
| Sprint brief | 600 words |
| Batch packet | 450 |
| Run prompt | 250 |
| Handoff | 150 |
| Checkpoint | 300 |

On context pressure: checkpoint ≤300 words → shrink → fresh session → reload checkpoint + brief + named paths only.

Full policy: [`core/orchestration.md`](../core/orchestration.md).
Material defect and mutation concerns: [`core/meeting-policy.md`](../core/meeting-policy.md).
Layered QA and promotion evidence: [`core/qa-operating-model.md`](../core/qa-operating-model.md).
