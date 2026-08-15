# Orchestration

Platform-agnostic coding-team flow. An **adapter** binds this core to a specific runtime; do not treat any IDE or agent host as the source of policy.

**One-line:** Lead (high reasoning) classifies nature, then orchestrates, plans, and delegates; specialists execute only that brief and tier; keep concurrency at ≤2 tool-using runs with Test Engineer → Gatekeeper sequential — never trial-error model hops or raising WIP to skip a causal chain.

## Lean / Agile nest (vocabulary only)

Standard Lean/Kanban/Agile names the management ideas; this framework remains the **agent runtime**. Do not replace Sprint→Batch→Task, role cards, model routing, or human gates with textbook Scrum/SAFe ceremonies.

| Our term | Lean / Agile cousin | Meaning here |
|---|---|---|
| WIP ≤2 | Kanban WIP limit | ≤2 concurrent tool-using runs — accelerate by smaller queued work + proven-disjoint parallels, never by raising the cap |
| Batch | Small batch | One integrable slice with known acceptance |
| Task | Work item / story slice | Spec-ready brief with stop condition |
| Sprint | Cadence / planning box | Coordination window — not story-point theater |
| PDCA + experiments + performance log | Kaizen | Root cause + named PIC → plan → observe → re-evaluate → **consolidate** (bake or close); see [learning-and-distillation.md](learning-and-distillation.md) |
| Gatekeeper after TE | Quality gate / Definition of Done | Evidence first; TE → Gatekeeper sequential |
| Human gates | Pull / stop-the-line | Irreversible actions need explicit human approval |

## Hierarchy

```text
Sprint  →  Batch  →  Task
```

| Level | Owns | Typical artifact |
|---|---|---|
| **Sprint** | Outcome theme, batch order, success criteria | `templates/sprint-brief.md` (≤ **600** words) |
| **Batch** | Integrated deliverable, owned files, validation plan | `templates/batch-brief.md` (≤ **450** words) |
| **Task** | Single role, exclusive scope, one handoff | `templates/task-brief.md` + run prompt (≤ **250** words) |

Encode Sprint ID, Batch ID, and task alias in each brief. Batch by dependency or shared contract — not role convenience. Detail only the first batch at sprint admission; keep later batches provisional until upstream evidence stabilizes.

## Lead authority

The **Lead** (parent orchestrator) is the only role that:

- Classifies **nature** (N0–N5 / Consult / Docs) and assigns **model tier**
- Opens/closes batches, admits tasks, and enforces WIP / gates
- Resolves Advisor vs Contradictor debates
- Synthesizes PM, Domain Advisor, System Architect, and specialist input into
  one recorded decision, owner, acceptance artifact, and next gate
- Routes defects to the classified owner as corrected briefs
- Does **not** implement product code or invent new roles

Incomplete or non-APPROVE outputs → **stop for human** ([human-gates.md](human-gates.md)).

### Scoped WYSY request intake

For a WYSY feature, function, or project-work request, the first accountable
owner is always **Lead**. This does not reclassify ordinary questions or
unrelated conversation. Lead records a serial consistency screen with:

1. **Product Manager** — problem, audience, outcome, scope, acceptance,
   success measure, and product risk; and
2. **System Architect** — architecture/state impact, shared-contract and
   migration/auth/privacy triggers, or an explicit no-contract reason.

The PM and System Architect remain canonical roles, not a standing panel. Their
checks are user-invoked and evidence-linked; Lead decides the route and may add
Advisor, Contradictor, Domain Advisor, UX, Investigator, Test Engineer, Docs
Steward, or Gatekeeper only when the existing concern/router policy triggers
them. A consistency screen never invokes a role, advances a stage, changes a
model map, or approves implementation automatically.

The intake relation is:

```text
scoped WYSY request → Lead → Product Manager → System Architect → Lead admission
```

The Project Graph records this relation. Monitor records the resulting
alignment, policy-cache, context-compaction, evidence, and gate observations;
it is not a router or authority source.

### Decision rule of thumb

Prioritize **user usability and practical usefulness** first. Then balance
**stability, reliability, and performance** for the admitted scope. A faster or
more elaborate path is not an improvement if people cannot use it safely or if
it makes the flow less dependable. Performance/cost claims remain measured,
estimated, or unavailable with named provenance; they are never inferred from
response length, elapsed time, or model tier.

### Lead cost discipline — emit judgment, not volume

The Lead runs the most expensive context in the system. Its output is classification, briefs, routing, verdicts on evidence, and short reports — never implementation code.

- **No typing lane:** a code block longer than an interface signature or a few illustrative lines is an undelegated spec — stop and delegate it to the owning builder.
- **Defects go back as briefs:** never hand-fix a builder's bug. Classify the failure and send a **corrected brief** to that owner.
- **Reason once, then hand off:** capture architecture/hypothesis thinking in the brief; do not re-derive it across turns.
- **Spec-readiness test:** a run prompt you cannot finish writing (objective, files, interfaces, constraints, verification) means the decision is not made yet. That is Lead/Advisor work — never delegate the ambiguity to a cheaper tier.

### Architecture-contract lane

Before allocating builders, the Lead dispatches `system-architect` when a
change establishes a shared multi-owner contract or crosses two or more of
FE, API, BE, and DB layers. The Architect freezes one named contract; the Lead
then allocates exclusive work and names the FIO. Builders implement against the
frozen contract, TE validates, and Gatekeeper decides. Material drift routes
**FIO → Lead → System Architect**. The Architect does not allocate, assemble,
implement, validate, or accept.

## Assignment fit and bounded execution

Apply this rule to every canonical role in this file. Before dispatch, Lead
checks that the task verb, evidence boundary, and reasoning fit the role
card's Purpose, Access, Duties, Stop conditions, and Never rules. A model,
free WIP slot, or manager's ability does not expand role capacity. If one task
mixes execution and synthesis, split it into two tasks. Give each task one
owner and one acceptance artifact. If no canonical role fits, return
`HUMAN_DECISION_REQUIRED`.

Every new or corrected Task brief must record these fields before dispatch:

| Field | Required value |
|---|---|
| `execution_scope` | One bounded verb, named paths/query/source set, output artifact, and explicit exclusions |
| `reasoning_depth` | `MECHANICAL`, `RECONCILE`, or `JUDGMENT` |
| `enumeration_required` | `true` or `false` |
| `synthesis_input_ref` | A completed Investigator packet path, or `NONE` |

`MECHANICAL` means locate, list, count, extract, or normalize without deciding
meaning. `RECONCILE` means follow bounded evidence or label a conflict without
choosing policy. `JUDGMENT` means decide, design, synthesize, validate, or
accept within the role. Set the field for the work that runs. Do not promote
mechanical work because its final decision is important.

Legacy briefs remain readable when these fields are absent. Treat each absent
field as `UNSPECIFIED`. Before a new policy-sensitive enumeration, Lead must
materialize all four fields. An `UNSPECIFIED` field with apparent enumeration
blocks dispatch and requires a corrected brief.

### Manager execution boundary

Manager roles are `lead`, `product-manager`, `system-architect`, `advisor`,
`contradictor`, and any `{domain}-advisor`. They may frame a question, name a
bounded source and query, state acceptance, compare supplied evidence, resolve
meaning, and emit a decision or contract. They must stop before they locate,
list, count, copy, or normalize source facts. Incidental reading of a named
excerpt is allowed. Expanding the source set or producing an enumeration is
not allowed.

Lead alone reconciles role outputs into the decision, owner, acceptance
artifact, and next gate. Lead may reject an insufficient packet or request a
corrected brief. Lead must not repeat the search. Investigator supplies facts
and conflicts. Investigator does not make policy, architecture, product,
validation, or acceptance decisions.

### Investigator routing and escalation

When `enumeration_required=true`, Lead creates a separate `investigator` Task
with a named path or query before manager synthesis. The packet states its
source boundary, requested fields, provenance format, stop condition, and
evidence artifact. A manager session is not an enumeration fallback. The
manager may synthesize enumerated facts only from the completed packet named by
`synthesis_input_ref`.

Use the existing escalation route for the next admitted Task. Keep a bounded
single-module mechanical lookup at Investigator / Tier 0. Return to Lead for a
corrected Investigator / Tier 1 brief when evidence conflicts, cross-file
tracing is needed, or a behavior or stateful trace is needed. Use a fitting judgment role
at Tier 2 only for a completed packet that raises a contract, architecture,
security, privacy, migration, release, or decision-changing conflict. Stop for
the existing human gate when no canonical role fits or scope needs secrets,
production, privacy, legal choice, irreversible action, or external provider
access. Context growth and missing telemetry do not cause a model hop.

### Checkpoint and telemetry boundary

Record `lookup_session_count`, `inspected_source_count`, and receipt input,
cached, and output fields when supplied. Set every missing receipt field to
`TELEMETRY_UNAVAILABLE` and record its source. Missing telemetry is not zero,
an estimate, or a cost claim.

Before a second lookup session, evidence-boundary expansion, a second
follow-up, the 75% artifact review trigger, `T_checkpoint` without a complete
artifact, or unexplained receipt growth without accepted evidence, stop and
write a bounded checkpoint. Include completed facts, evidence references,
unavailable fields, one unresolved item, and exactly one next Task. At the 75%
trigger, compress only the handoff packet or stop. At `T_hard` set the Task
to `BLOCKED`. Do not silently continue, retry, expand scope, or change model.

Monitor records an observational projection of the assignment fields, parent
and worker task/role IDs, planned-to-actual tier/model/effort, bounded source
set, inspected-source count, lookup-session count, checkpoint or escalation
reason, evidence reference, result, and receipt input/cached/output or
`TELEMETRY_UNAVAILABLE` with source. Monitor records compliance. It does not
route, act, or become a competing fact source.

## Canonical role IDs

Use only these IDs (see `roles/`):

| ID | Role |
|---|---|
| `lead` | Lead |
| `product-manager` | Product Manager |
| `system-architect` | System Architect |
| `advisor` | Advisor (technical, pre-build) |
| `contradictor` | Contradictor |
| `domain-advisor` | Domain Expert **template** → instances `{domain}-advisor` (see [domain-advisors.md](domain-advisors.md)) |
| `investigator` | Investigator |
| `monitor-agent` | Monitor Agent (run trace and cost visibility) |
| `backend-engineer` | Backend Engineer |
| `frontend-ux-lead` | Frontend UX Lead |
| `frontend-builder` | Frontend Builder |
| `test-engineer` | Test Engineer |
| `docs-steward` | Docs Steward |
| `gatekeeper` | Gatekeeper |

Never invent a new role **family**. Instantiating `[Domain]-Advisor` from the `domain-advisor` template (after the human names the domain) is allowed and required when domain consult is needed.

### Alias normalization (do not invent role families)

| Incoming label | Route to |
|---|---|
| Explorer | `investigator` |
| Inspector — repository/config/artifact facts | `investigator` |
| Inspector — test or validation evidence | `test-engineer` |
| Inspector — final independent decision | `gatekeeper` |
| Reviewer — final independent review | `gatekeeper` |
| Reviewer — non-final domain/UX/code feedback | Existing accountable functional owner |
| Pre-build technical judgment | `advisor` |
| Backbone, framework, API, data, or shared-contract ownership | `system-architect` |
| Pre-build challenge | `contradictor` |
| Talent / Talent-Career / employment-domain consult | `talent-advisor` (Domain Advisor instance) — or **ask** if domain unclear |
| Strategic / strategy consult | `strategic-advisor` — or **ask** |
| “Domain expert” / “specialty advisor” with no domain | **Ask human** for domain → `{domain}-advisor` |

If no predefined role or Domain Advisor instance can safely own the task → `HUMAN_DECISION_REQUIRED`.

## Context caps (hard)

| Artifact | Max words |
|---|---|
| Sprint brief | **600** |
| Batch brief | **450** |
| Task run prompt | **250** |
| Handoff | **150** |
| Batch checkpoint | **300** |

Prefer path/line evidence pointers over pasted dumps. Shrink the packet before escalating tier. Default each specialist run to a **fresh** session; continue only for one immediate follow-up that depends on unpersisted local reasoning and still fits the cap.

### Context-compaction sweet point (provisional)

Context compaction is a Lead-owned packet rewrite, not a role, router, retry,
or permission to drop evidence. Keep the smallest packet that preserves the
objective, identity, scope/owned paths, acceptance, evidence refs and status,
unresolved unknowns, last decision, and exactly one next action. Do not paste
raw transcripts or reproduce source dumps.

Use these bounded targets while `EXP-S2-CONTEXT-COMPACT-001` is open:

| Artifact | Hard cap | Sweet-point target (60%) | Review trigger (75%) |
|---|---:|---:|---:|
| Sprint brief | 600 | 360 | 450 |
| Batch brief | 450 | 270 | 338 |
| Batch checkpoint | 300 | 180 | 225 |
| Task run prompt | 250 | 150 | 188 |
| Handoff | 150 | 90 | 113 |

The 60% value is an explicit operating hypothesis, not measured token
efficiency. At the 75% review trigger, Lead either compresses the packet into
the target band or stops with a bounded checkpoint; it never silently extends
the context or discards unresolved evidence. A host compaction or new
conversation requires a fresh policy-cache identity and policy read before a
policy-sensitive action; rotate the context fingerprint as specified by
`core/policy-cache.md`.

The compact packet must carry `packet_revision`, `source_refs`,
`verified_facts`, `reasoned_or_unknown`, `decision`, `next_action`, and
`compaction_status=PROVISIONAL|VALIDATED|REJECTED`. `PROVISIONAL` remains local
until five independent observations satisfy the experiment's retention,
correction, and re-read measures. No compact packet changes role ownership,
model routing, workflow stage, gate state, or `auto_action=none`.

## Task-size metric: when to split instead of waiting

Task timing uses the active approved profile defined by
[adaptive-timing.md](adaptive-timing.md): `T_target = target_s`,
`T_checkpoint = checkpoint_s`, `T_hard = hard_stop_s`, and
`T_reserve = reserve_s`, with
`T_target < T_checkpoint < T_hard`. If the profile is invalid or unavailable,
select its versioned fallback and state remediation; no timing value below is
a universal cap.

“Long” is an operational threshold, not a feeling. Before allocation, price
the plan as `T_plan = T_setup,p95 + ΣT_mutation-unit,p95 +
ΣT_validation-command,p95 + T_handoff,p95`; every duration must carry exactly
one provenance label: `MEASURED`, `ESTIMATED`, or `UNKNOWN`, plus its source,
class, and conditions. If any mandatory duration is `UNKNOWN`, `MEASURE` it
within a bounded package before dispatch. Use the action set
`ADMIT|MEASURE|SPLIT|BLOCK` with this precedence: mandatory `UNKNOWN` →
`MEASURE`; validation beyond `T_hard - T_reserve` or failed checks → `BLOCK`;
then `T_plan <= T_target` → `ADMIT`, otherwise → `SPLIT`. An atomic,
measured-p95 plan may exceptionally be admitted only when
`T_plan + T_reserve < T_hard`.

Measure from role start to the first complete artifact or stop reason
(excluding human approval or queue wait). A Task is **too long** when it is
expected to exceed `T_target`, reaches `T_checkpoint` without a
complete artifact, or needs a second follow-up after its one permitted
immediate handoff. At `T_hard` it is `BLOCKED` and must stop; `T_checkpoint`
is checkpoint-only and `T_hard` is safety-stop-only.

A Task is **too wide** when any of these is true:

- it has more than one accountable role or more than one independent concern;
- it needs non-disjoint writers, crosses an unstable shared contract, or has no
  single acceptance artifact;
- its run prompt would exceed 250 words, its handoff would exceed 150 words,
  or the stop condition cannot be stated in one sentence.

Before starting, split a too-long/too-wide Task into dependency-safe slices
with exclusive files, one owner, one acceptance artifact, and one stop
condition. Concurrent branches are permitted only for frozen scenarios,
disjoint resources, and recorded independence evidence; otherwise price them
sequentially. During a run, emit a checkpoint at `T_checkpoint` or when a metric
is crossed: completed work, evidence, unresolved question, and exactly one
next bounded Task. On timeout, record plan/elapsed time, phase,
completed/pending work, result, environment/resources, and one next owner:
workload → builder; validation → TE; environment/dependency → Lead;
ambiguity → Lead → Architect. The Lead hands that slice off; it does not
silently extend the context, retry the same mutation loop, or leave the
original Task frozen. A retry must change scope, dependency, tool route, or
environment; an unchanged retry is `BLOCK`/`SPLIT`.

## Skill loading

- **Start with none.** Load skills only when the task brief names them (or the role card’s “load when” trigger matches).
- Paths are relative to this repo: `skills/engineering/…`, `skills/quality/…`, `skills/process/…`, `skills/design/…`.
- One primary skill per task; a second requires a separately recorded unresolved question.
- Do not auto-load every skill because Lead or multi-agent work is happening.
- The stable policy bundle is a separate session/context concern. The Codex
  adapter may reuse an unchanged policy manifest after a verified cache `HIT`,
  but this does not cache task facts, role-card bytes, system instructions, or
  host tools. A missing/changed policy file, new session, context loss or
  compaction, high-risk/learning trigger, or human refresh request requires a
  fresh policy read. `BYPASSED`/`UNAVAILABLE` fails closed for policy-sensitive
  delegation. Record cache/timing/token provenance in the local Monitor
  receipt; never infer provider savings from a cache hit.

### Skill overrides

Brief triggers override upstream skill “When to Activate” / auto-discovery language. Do not rewrite upstream skill bodies wholesale.

1. **`context-engineering`** — Load **only** when the brief trigger is: create/revise a context packet, bounded investigation, or cross-role synthesis. Never auto-load because Lead, Advisor, multi-agent, or debate work is happening.
2. **`sequential-thinking`** — If host MCP reasoning tools are unavailable: structured written steps in the handoff still satisfy the second-failure skill; do not invent MCP tools.
3. **`problem-solving`** — Exception-only after known root cause or genuine design deadlock; never replace `debugging` for concrete failures.

Advisor / Contradictor default primary skill is `none`. Model tier assignment is orthogonal to skill load.

## Cheap-utility cost tier (pool-mapped)

Prefer the host’s **Tier 0** mapped slug (Codex often maps this to a Luna-class model) for cost-sensitive, high-volume `S0`/`S1` work with an explicit output, bounded evidence or file boundary, and a named stronger owner for synthesis or escalation.

**Default cheap-utility roles / cells:** Investigator; low-risk single-boundary Frontend Builder; eligible temporary support cells (evidence/citation collection, request classification, assumption inventory, stakeholder-lens extraction, dependency/status aggregation, synthetic fixtures, focused test support, failure-log triage).

**Do not** use cheap-utility as the accountable default for Lead, PM, Backend, Frontend/UX contract ownership, Test Engineer validation synthesis, Docs Steward governed docs, or Gatekeeper. Escalate Tier 0 → Tier 1 build/validate when evidence conflicts, scope crosses modules, behavior is statefully complex, validation fails, or accessibility/security/privacy/public-contract implications appear. Escalate to Tier 2/3 only under recorded high-risk triggers in [model-routing.md](model-routing.md).

## Functional Integration Owner (FIO) overlay

**FIO is a temporary responsibility overlay on one existing canonical
implementation role, not a role ID.** The role registry, role cards, model map,
and adapter delegation table must never contain `fio`. The Lead records the
overlay in the Batch brief before build:

- `scope`: `frontend`, `backend`, `cross-layer`, `ux-contract`, or `none`
- one `integration_seam` and one canonical `fio_role_id` plus its task ID, or
  `NONE` when no seam exists
- the FIO's exclusive paths, frozen `contract_ref` and hash when applicable,
  and `fio_status`

Assignment follows the primary seam. A Frontend Builder carries a frontend
seam, a Backend Engineer carries an API/data seam, and the role owning the
primary seam carries a cross-layer overlay. A single-task Batch may set the
task owner as FIO without creating another task or ceremony. Docs,
consultation, architecture-only, evidence-only, and no-seam Batches use
`FIO = NONE`. A Batch must never name two FIOs; split independent seams or
return to Lead for a new decision.

FIO owns only the admitted seam: it may read the frozen contract and named
handoffs, and may write only its own exclusive paths. It does not manage or
reassign teammates, broaden scope, amend the architecture contract, edit
another owner's paths, replace the System Architect, or issue TE/Gatekeeper
decisions. Material contract or invariant drift routes **FIO → Lead → System
Architect**; an ordinary defect returns as a corrected brief to its canonical
owner. FIO reports `NOT_ASSIGNED`, `IN_PROGRESS`, `READY_FOR_TE`,
`DRIFT_REPORTED`, or `BLOCKED` and hands the seam to an independent TE. FIO
`READY_FOR_TE` is never TE evidence or acceptance.

There is no FIO skill or model tier. The overlay inherits the canonical
owner's named skills and planned→actual model/effort. It must not auto-load
skills or escalate a model merely because the assignment is called FIO.

## Default batch shape

1. Brief + nature/tier classification
2. Triggered concern method + consult: choose the smallest fitting method, start with one accountable role, and add one decision-changing specialist at a time (per [model-routing.md](model-routing.md)); use the bounded meeting rules in [meeting-policy.md](meeting-policy.md) for material defects, state risks, or cross-role conflicts
3. Conditional acceptance design: PM `user-stories`/`pre-mortem` when triggered + Domain Advisor input → pre-build Test Engineer scenario matrix
4. Human gate when required ([human-gates.md](human-gates.md))
5. Builders (WIP ≤ 2; exclusive files — [concurrency.md](concurrency.md))
6. **Test Engineer** evidence in a fresh post-integration context
7. **Gatekeeper** accept / revise / block
8. Docs Steward if durable docs are in scope

Use acceptance design for user-facing workflows, input parsing/matching, AI
extraction, public contracts, or materially ambiguous acceptance. PM supplies
user outcomes, personas, and acceptance criteria; a Domain Advisor supplies
named-domain meaning only when triggered. Test Engineer freezes an observable
scenario matrix before builders. It is implementation input, not final TE
evidence. For suitable deterministic unit, contract, or component cases,
builder briefs require selective red-green-refactor; do not force E2E-first.

### Corrective batch loop

Each Test Engineer or Gatekeeper pass collects all in-scope findings before
issuing its result; Lead does not dispatch fixes mid-pass. Human approval
enumerates correction scope; new defects or scope expansion require a new gate.
Cluster findings by demonstrated root cause, never symptom similarity. Keep a
corrective Batch one integrable slice; queue cross-contract findings as
provisional Batches. Preserve or add one failing regression per finding where
feasible, reintegrate once, then run targeted checks, affected regressions,
independent negative/adversarial cases, and Batch acceptance. A fresh Test
Engineer validates before one sequential Gatekeeper re-review. Final TE
`FAIL`/`BLOCKED`, insufficient fresh evidence, or a Gatekeeper verdict outside
`APPROVE`/`APPROVE_WITH_NOTES` stops for the human gate.

For the full participant, artifact, and PDCA rules, use
[meeting-policy.md](meeting-policy.md). “Test all” means the complete frozen
Batch matrix, not an unbounded repository-wide rerun.

### Learning and distillation

At material Batch and Sprint close, Lead records an evidence-linked learning
disposition using [learning-and-distillation.md](learning-and-distillation.md).
Monitor Agent capture is observational only. A single observation remains a
candidate; durable policy, routing, skill, template, security, privacy, or
public-contract promotion requires the validation and human-gate rules in that
policy. Never create a standing learning/consolidation role or silently mutate
core policy from a run.

## WIP, rotation, and context economy

Default WIP:

- one `ACTIVE` sprint
- one `ACTIVE` implementation batch and one next `READY` batch
- ≤2 concurrent tool-using specialists total (including Investigator)
- one active write task per role; one writer per file
- no reserved “support lane” that bypasses the task list

Parallel tasks require satisfied dependencies, stable contracts, disjoint files, own acceptance, and known integration order. Fake parallel is a Lead planning defect.

Do not create standing coordinators, shadows, helpers, or consolidation agents. Every contributor owns a normal task-list item with exclusive deliverable and stop condition. When queueing blocks the critical path, re-sequence or split — optionally use cheap-utility temporary cells under the same WIP cap with one accountable synthesizer.

If a task is too wide for one bounded run, split it into small dependency-safe
Tasks with exclusive files, explicit acceptance, and a stop condition. Hand off
the completed slice with evidence, unresolved questions, and the next bounded
Task. Do not leave an oversized task frozen, silently extend its context, or
restart it without a checkpoint.

Urgent work uses an explicit **expedite batch** after checkpointing the active batch — never silent injection.

## Time budget and semantic status

- Target `T_target` when practical
- At `T_checkpoint` → `PARTIAL` with evidence, unresolved question, next bounded step
- At `T_hard` → cancel or split rather than waiting out the provider
- Bounded QA uses the active profile's `T_target` / `T_hard`. A timed-out validation
  records `BLOCKED` evidence and one next action; Lead hands off one smaller
  follow-up Task instead of leaving the batch frozen. It never auto-retries or
  starts Gatekeeper.
- Transport `completed` with empty/malformed/timeout content → `FAILED_TRANSIENT` (not accepted work)

## Adapter note

Runtime wiring (how tasks are spawned, which model pool is used, how approvals are collected) lives under `adapters/`. **Adapter binds runtime** — core policy here stays host-independent.
