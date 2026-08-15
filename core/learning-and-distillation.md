# Learning and distillation policy

This policy turns completed Coding Team work into bounded, reusable knowledge.
It is a policy overlay on Sprint → Batch → Task; it is not a second router,
memory runtime, role family, or permission to change product behavior.

## When it runs

Record a learning disposition at every material Batch close and Sprint close.
For a low-risk Batch with no useful signal, record `NONE` in the final report.
Run the full flow when any of these occurs:

- a Test Engineer or Gatekeeper finding, revise, block, or repeated failure;
- a user correction, domain clarification, or changed acceptance decision;
- a model/tier substitution, cost, latency, or quality experiment;
- an incident, escaped defect, or recurring friction pattern; or
- an explicit request to improve policy, prompts, skills, routing, or templates.

Open an experiment only when there is one falsifiable hypothesis, a named
owner, a success measure, a stop/revert criterion, a review point, and a
bounded out-of-scope list. Keep at most **three** open `EXP-*` records.

## Learning versus distillation

- **Learning** is an evidence-linked observation: what happened, where, under
  which scope, and with what outcome. It may be local and provisional.
- **Distillation** is the bounded claim extracted from one or more learning
  records, with applicability, confidence, and a verification plan. It is not
  a summary of a transcript and must not add unsupported causes.
- **Promotion** is the separately approved act of baking a distilled claim into
  core policy, an adapter overlay, a project rule, a skill, a template, or
  routing guidance.

One observation is a candidate, not a general rule. A recurring pattern needs
two independent supporting observations or an explicit human decision. A
material policy, routing, security, privacy, or public-contract change always
needs a human gate; silence is not approval.

## Lifecycle and ownership

| Stage | Owner | Required result |
|---|---|---|
| Capture | Monitor Agent when available; otherwise Lead | Source-linked observation and outcome |
| Normalize | Lead | Separate fact, interpretation, and unknown; remove secrets and unnecessary personal data |
| Correlate | Lead, using the smallest fitting concern method | Demonstrated shared cause or explicitly separate signals |
| Distill | Lead | One bounded lesson, scope, confidence, and cheapest validation |
| Validate | Test Engineer for behavior/process claims; relevant owner for other claims | Fresh evidence, repeat evidence, or documented human decision |
| Promote or close | Human approves material promotion; Docs Steward records accepted durable docs | One disposition: promote, keep local, retest, supersede, or close |

The Monitor Agent may record traces, costs, graph facts, and evidence pointers,
but has no acceptance, routing, or policy authority. The Lead may propose a
distillation but may not silently mutate core policy or model routing. Docs
Steward writes only the named approved documentation path.

## Experiment / PDCA contract

Experiments are evidence containers, not an alternate execution router. The
allowed states are `OPENED` → `CONTINUE` | `SUCCESSFUL` | `REVERTED`.

Each `EXP-*` record contains:

- hypothesis, owner/PIC, baseline, success measure, and review point;
- stop/revert criteria and explicit out-of-scope boundaries;
- planned→actual model/tier and fallback mode when relevant;
- evidence refs to the run, TE/Gatekeeper, performance log, or decision pack;
- a human decision for continue, successful, or reverted; and
- any resulting learning/distillation entry.

`CONTINUE` is a proposal until the human decision is recorded. An experiment
does not authorize scope expansion, model escalation, policy mutation, or
shipping. Experiment evidence never replaces fresh TE evidence or Gatekeeper.

## Fallback reasoning capture

When a lower-tier model substitutes for a role's planned model, declare one
mode: `FULL`, `REDUCED_SCOPE`, `READ_ONLY`, or `PLANNING_ONLY`. The handoff
must separate verified evidence, reasoned-but-untested claims, and unverified
items. Capture an improvement event when the fallback is corrected, lacks
evidence, is blocked, or reveals a reusable pattern. Promote only after
supporting evidence and the applicable human gate.

## Required evidence boundary

Every learning or distillation entry points to the run, Batch/Sprint, exact
validation or gate artifacts, and relevant commit/revision when available. Keep
raw transcripts, secrets, credentials, and unnecessary personal data out of
durable records. Record unavailable telemetry as unavailable; never infer cost,
quality, or model identity from a proxy and call it measured.

Use these claim classes:

| Class | Meaning | Default disposition |
|---|---|---|
| `FACT` | Directly observed and reproducible | Keep with source refs |
| `PATTERN` | Supported by independent observations | Validate before promotion |
| `HYPOTHESIS` | Plausible explanation or proposed change | Run the cheapest bounded test |
| `DECISION` | Human- or Gatekeeper-approved scope decision | Record approver and expiry/review trigger |

## WYSY public-repository data boundary (candidate)

For the WYSY internal trial, learning and distillation records use a nested
default-deny boundary: `storage_scope=LOCAL_ONLY`,
`export_status=NOT_REQUESTED`, `public_safe=false`, `consent_ref=null`, and
`redaction_check=NOT_RUN`. Raw requests and PM drafts may remain in a local
flow packet but are never public-safe by default. A future public-safe record
may contain only generic sanitized outcomes, stage/status, aggregate metrics,
cost provenance, and safe evidence references. Never export source code, diffs,
raw prompts/PRDs, transcripts, secrets, credentials, provider/account
identifiers, PII, private payloads, or sensitive paths.

Any future export requires explicit per-run human consent, a passing redaction
check, and a manifest; absent those preconditions it must fail closed. This is a
candidate data boundary for the WYSY trial, not a promoted distillation rule,
network exporter, training pipeline, or permission to change core policy.

## Promotion rules

Choose the narrowest destination that solves the demonstrated problem:

1. no durable change — close the record;
2. task-specific reminder — keep in the handoff or batch checkpoint;
3. repeated execution guidance — update a skill or template;
4. host-specific behavior — update the adapter or project overlay;
5. cross-host invariant — update `core/` only after human approval and focused
   validation; and
6. model/tier guidance — update routing only with comparable outcome evidence,
   including quality and cost availability status.

Never promote a single anecdote, an unverified synthetic benchmark, a stale
fact, or a Gatekeeper result into a general policy. Every promoted entry names
its scope, effective date, owner, validation evidence, and revalidation or
expiry trigger. A later contradiction supersedes the claim through the same
process; it does not get silently edited away.

## Bounded candidate confidence, decay, and concern coverage

WYSY now approves a deterministic **Learning Review** evaluator as a bounded
implementation candidate. It scores a Learning Candidate for review; it does
not score the model, authorize a role, route a task, mutate a skill, or promote
policy. The Monitor ledger is the canonical fact source, and Flow Bench is only
the scenario/replay producer.

The evaluator uses explicit 0–100 components and publishes the calculation:

```text
candidate_confidence =
  outcome_improvement × 0.30
  + gatekeeper_impact × 0.25
  + repeatability × 0.20
  + evidence_strength × 0.15
  + sample_size × 0.10
```

`sample_size` is derived from observations against a preferred 20-observation
reference; five observations is the minimum promotion eligibility. Tiers are
`EXPERIMENTAL` (0–40), `PROBATION` (41–70), `TRUSTED` (71–90), and
`PROMOTION_CANDIDATE` (91–100). These are review labels, not probabilities or
automatic thresholds.

Decay is a review signal, never silent subtraction or deletion:

- `CURRENT`: no contradiction and review not due;
- `REVIEW_DUE`: the candidate's explicit review date has arrived;
- `WEAKENED`: a recent quality or success trend is worse than its baseline;
- `CONTRADICTED`: an independent result conflicts with the claim;
- `STALE`: the evidence cannot be revalidated within its stated scope.

Each signal records its reason, evidence refs, next review, and a human-only
action (`KEEP`, `MONITOR`, `DOWNGRADE`, `RETEST`, `RETRAIN`, `SUPERSEDE`, or
`RETIRE`). `RETRAIN` creates a new candidate; it never launches training.

Concern coverage is diagnostic for the canonical technical, process, product,
and security lenses. It can show `COVERED`, `PARTIAL`, `UNRESOLVED`,
`CONTRADICTED`, or `NOT_APPLICABLE`, but it cannot assign a reviewer, role,
model, or escalation. Promotion still requires at least five observations,
independent evidence, a positive Gatekeeper trend, no major contradiction, a
baseline/negative/holdout/falsifier, fresh TE evidence, Gatekeeper review, and
explicit human approval. The source skill remains unchanged until Docs Steward
records the approved, scoped addendum.

## Artifact

Use [`templates/learning-entry.md`](templates/learning-entry.md) for the
capture-to-disposition record. Link it from the final report, checkpoint, or
run trace. `NONE` is a valid disposition only when the close report states the
reviewed sources and why no reusable signal was found.

Use [`templates/experiment-entry.md`](templates/experiment-entry.md) for an
`EXP-*` record and [`templates/distillation-entry.md`](templates/distillation-entry.md)
for a concrete fallback or project lesson. Extend
[`templates/performance-entry.md`](templates/performance-entry.md) when a
substitution or experiment produces routing/cost evidence.
