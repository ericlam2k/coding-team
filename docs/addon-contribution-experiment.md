# Addon contribution experiment

## Purpose and boundary

Evaluate whether optional Caveman and Ponytail improve naturally occurring Coding Team work. This protocol is experimental and non-orchestrating: it does not duplicate implementation, change core routing, alter WIP, replace Test Engineer or Gatekeeper, or require per-task human approval. Both addons remain default OFF outside a deliberately assigned study arm.

Upstream Caveman token-savings claims are not local evidence. Ponytail may overlap the core minimal-diff policy; measure contribution rather than assume it.

## Arms and sampling

Use these arms only on comparable, eligible tasks that would occur anyway:

| Arm | Addon state |
|---|---|
| Core-only | Neither addon |
| Caveman | Caveman only |
| Ponytail | Ponytail only |
| Both | Caveman and Ponytail |

Alternate arms only within comparable task type and risk. Do not manufacture work, split a task, repeat an implementation, or use an addon where it is plainly irrelevant. Collect at least 8 eligible tasks total, with at least 2 per arm; extend collection when the task-type or risk mix is imbalanced.

## Per-task record

Copy this record into the [results ledger](addon-contribution-results.md) after the normal task outcome is known:

```text
| Task ID | Type | Risk | Arm | Host tokens / proxy | Wall time | Calls | Files / LOC | Clarifications / revisions | TE defects / verdict | Gatekeeper verdict | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

Record actual host token usage when available. Otherwise record an explicitly labelled output-word proxy; it is directional evidence only. Record wall time, calls, changed files/LOC, clarification and revision counts, Test Engineer defects/verdict, and Gatekeeper verdict without treating the ledger as acceptance evidence.

## Decision rule

After the minimum balanced sample, make one consolidated recommendation, not a per-task approval. A useful-cost signal means the median cost evidence for comparable tasks that reached no worse Test Engineer and Gatekeeper outcomes. Keep an addon enabled for further use only when the median useful-cost signal improves by at least 10% versus comparable core-only tasks and no material quality or gate regression occurs. Confirm any proxy-only result with host token data before calling it a proven token saving.

Any material quality regression, increased gate failure, or worse Test Engineer outcome prevents adoption. If the threshold is not met, keep the addon optional or remove it when it shows no contribution. See the [results ledger](addon-contribution-results.md) for collection and the pending recommendation.
