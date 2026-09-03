# Agentic Worker addon benchmark

## Purpose

Measure whether the optional `agentic-worker` overlay improves bounded
app-development work without weakening evidence, safety, or human gates.

This is an experiment, not a core-policy change. The addon remains reversible
and default OFF unless explicitly enabled.

## Conditions

Use the same task, repository revision, model family, tool access, context
budget, and time limit.

| Condition | Description |
|---|---|
| Core | Coding Team flow without Agentic Worker |
| Agentic Worker | Same flow with the explicit worker overlay |
| Parallel comparison | PM method and CPS method run concurrently in separate read-only workspaces when the task is genuinely complex |

Do not run two writers against the same files. Parallelism is for independent
analysis or disjoint work only, and WIP remains ≤2.

Use at least three repetitions per comparable condition when the host is
nondeterministic. Report median, range, denominator, and hard failures.

## Metrics

### Quality and safety

- verification pass rate;
- seeded defect detection rate;
- evidence completeness;
- unauthorized assumptions and decisions;
- provenance violations;
- Test Engineer defects and Gatekeeper verdict;
- human review time;
- rework cycles.

### Speed and efficiency

- total wall-clock makespan;
- per-track active time;
- queue/wait time;
- host tokens and cost, when available;
- changed files and source churn;
- tool/model calls.

If token telemetry is unavailable, record `UNAVAILABLE`. Word count is only a
labelled directional proxy, never a token-saving claim.

## Parallelism calculations

```text
wall_speedup = serial_makespan / parallel_makespan
parallel_efficiency = wall_speedup / number_of_tracks
useful_cost = tokens_or_cost for runs with no worse TE/Gatekeeper outcome
```

Parallel is better only when it reduces makespan or improves decision quality
without unacceptable increases in total cost, rework, false positives, or gate
failures. Lower wall time alone does not prove higher efficiency.

## Decision rule

Keep Agentic Worker enabled for further app-development use only when the
median useful-cost signal improves by at least 10% versus comparable core-only
tasks and there is no material quality or gate regression. If telemetry is
unavailable, report the quality result but make no cost or productivity claim.

## Required plain-English summary

After a PM-versus-CPS parallel comparison, report:

```text
Decision summary
- Task:
- PM result:
- CPS result:
- Agreement/disagreement:
- Quality and safety:
- Time and token/cost data:
- Rework and review burden:
- Is parallelism actually more efficient? why?
- Recommendation:
- Human decision required:
```
