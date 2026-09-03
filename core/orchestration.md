# Orchestration

Platform-agnostic coding-team flow. An **adapter** binds this core to a specific runtime; do not treat any IDE or agent host as the source of policy.

**One-line:** Lead (high reasoning) classifies nature, then orchestrates, plans, and delegates; specialists execute only that brief and tier; after integration, bind deterministic evidence → Code Reviewer → conditional Test Engineer → final Gatekeeper, with WIP ≤2 ordinary workers (+≤1 supervisor relay) and every required Test Engineer → Gatekeeper pair sequential — never trial-error model hops or using supervision as a third work lane.

## Lean / Agile nest (vocabulary only)

Standard Lean/Kanban/Agile names the management ideas; this framework remains the **agent runtime**. Do not replace Sprint→Batch→Task, role cards, model routing, or human gates with textbook Scrum/SAFe ceremonies.

| Our term | Lean / Agile cousin | Meaning here |
|---|---|---|
| WIP ≤2 + supervisor ≤1 | Kanban WIP limit | ≤2 concurrent ordinary runs plus one bounded read-only relay when admitted — accelerate by smaller queued work, never by making supervision a third work lane |
| Batch | Small batch | One integrable slice with known acceptance |
| Task | Work item / story slice | Spec-ready brief with stop condition |
| Sprint | Cadence / planning box | Coordination window — not story-point theater |
| PDCA + experiments + performance log | Kaizen | Root cause + named PIC → plan → observe → re-evaluate → **consolidate** (bake or close) |
| Gatekeeper after routed evidence | Quality gate / Definition of Done | Evidence first; conditional TE and final Gatekeeper follow the QA route |
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

### Lead request shaping — one feasible slice

When an incoming request is broad, ambiguous, or spans more than one concern,
the Lead makes one bounded shaping decision against the existing Sprint, Batch,
and Task fields. This is planning input only; it adds no lifecycle state and no
second acceptance or admission path. Read current briefs, contracts, owned
paths, acceptance, dependencies, prior blockers, and the timing profile first.
Reuse that evidence instead of creating duplicate product or technical forms.
For a low-risk gap, record a reversible assumption with its evidence, owner, and
undo condition. Ask a human only when the answer changes product behavior,
priority, user outcome, public contract, or an irreversible action.

Return exactly one shaping disposition:

- **`SINGLE`** — one accountable role, one concern, one acceptance artifact,
  exclusive paths, and satisfied prerequisites. Render one selected slice.
- **`SPLIT`** — independent concerns, multiple owners/non-disjoint paths, or a
  bounded-size violation. Order by prerequisites, render the first
  dependency-safe slice, and queue the remainder with owner, prerequisite, and
  state. Queueing does not dispatch work.
- **`CLARIFY`** — one missing product or irreversible choice changes the slice.
  Ask at most one plain-language question, route it to PM/human, and retain the
  request at the existing intake point. Do not claim readiness or dispatch.
- **`MEASURE`** — required feasibility or timing evidence is missing or only
  estimated. Use the existing adaptive-timing measurement route; do not dispatch
  the implementation slice until its evidence is measured.
- **`BLOCK`** — a prerequisite, gate, contract, evidence, owner, or prior
  hard-stop condition prevents a safe slice. State what/why/where for Lead or
  human; do not dispatch.

`SINGLE` and `SPLIT` select exactly one slice before
`prepare-dispatch.py`; `CLARIFY`, `MEASURE`, and `BLOCK` select none. The
shaping disposition does not replace workload admission: the existing
`ADMIT|MEASURE|SPLIT|BLOCK` rules in `adaptive-timing.md` still decide whether a
prepared slice may run. `prepare-dispatch.py` validates packet identity and
shape; it does not design the request, choose its slice, approve work, or admit
it. Supervision starts only after Lead admission, and a preflight `READY` result
is not admission or supervision.

### Lead cost discipline — emit judgment, not volume

The Lead runs the most expensive context in the system. Its output is classification, briefs, routing, verdicts on evidence, and short reports — never implementation code.

- **No typing lane:** a code block longer than an interface signature or a few illustrative lines is an undelegated spec — stop and delegate it to the owning builder.
- **Defects go back as briefs:** never hand-fix a builder's bug. Classify the failure and send a **corrected brief** to that owner.
- **Reason once, then hand off:** capture architecture/hypothesis thinking in the brief; do not re-derive it across turns.
- **Spec-readiness test:** a run prompt you cannot finish writing (objective, files, interfaces, constraints, verification) means the decision is not made yet. That is Lead/Advisor work — never delegate the ambiguity to a cheaper tier.

### Terminal closeout is required

Every completed, blocked, cancelled, or partial Task must state both fields in
`templates/handoff.md`:

1. **Recommended next to-do:** exactly one bounded Task, human decision, or
   `NONE — objective complete`.
2. **Pending tasks:** `NONE`, or a compact queue with owner, prerequisite, and
   state.

Before Lead treats a terminal handoff as closed, run
`python3 core/tools/validate_terminal_closeout.py` against the rendered handoff. A
validator failure means **not closed** and stops task progression. Lead may ask
the same owner for one format-only correction; this is not a retry, a new task,
or permission to change scope. If a truthful closeout needs a new decision,
new evidence, or an unavailable owner, stop for the human. The validator checks
presence and shape only. It does not approve a gate, choose product scope, or
dispatch queued work.

### Architecture-contract lane

Before allocating builders, the Lead dispatches `system-architect` when a
change establishes a shared multi-owner contract or crosses two or more of
FE, API, BE, and DB layers. The Architect freezes one named contract; the Lead
then allocates exclusive work and names the FIO. Builders implement against the
frozen contract, the QA route supplies evidence, and Gatekeeper decides. Material drift routes
**FIO → Lead → System Architect**. The Architect does not allocate, assemble,
implement, validate, or accept.

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
| `monitor-agent` | Monitor Agent — bounded read-only supervisor relay |
| `backend-engineer` | Backend Engineer |
| `frontend-ux-lead` | Frontend UX Lead |
| `frontend-builder` | Frontend Builder |
| `code-reviewer` | Code Reviewer |
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
| Reviewer — post-integration code/evidence review | `code-reviewer` |
| Reviewer — final acceptance decision | `gatekeeper` |
| Reviewer — non-final domain/UX feedback | Existing accountable functional owner |
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

Prefer path/line evidence pointers over pasted dumps. Shrink the packet before
escalating tier. Default each new Task to a **fresh** session. A same-task
continuation may safely reuse context only when identity, scope, permissions,
policy, and evidence remain current and the corrected brief records a material
delta; follow [adaptive-timing.md](adaptive-timing.md).

## Task-size metric: when to split instead of waiting

Task timing uses the active approved profile defined by
[adaptive-timing.md](adaptive-timing.md): `T_target`, `T_checkpoint`, `T_hard`,
and `T_reserve`, with `T_target < T_checkpoint < T_hard`. If the profile is
invalid or unavailable, select its versioned fallback and state remediation;
no planning bound below is a universal constant.

Before allocation, price `T_plan = T_setup,p95 +
ΣT_mutation-unit,p95 + ΣT_validation-command,p95 + T_handoff,p95`.
`T_setup,p95` includes required policy, memory, migration, and repository
bootstrap. Every duration records `MEASURED`, `ESTIMATED`, or `UNKNOWN`, plus
source, class, and conditions. `MEASURED` requires a receipt. Mandatory
`UNKNOWN` returns `MEASURE` without dispatch. `ESTIMATED` also returns
`MEASURE` without dispatch. Record candidate path count and prior-hard-stop
state. Candidate-wide verification must be a separate receipt, not hidden in a
narrower task. `prior_hard_stop=true` is route-specific and returns `BLOCK` for
that unchanged route; after reconciling authoritative state, Lead may price one
materially changed smaller route under `adaptive-timing.md` without treating
the whole objective as blocked.

“Long” is an operational threshold, not a feeling. Measure from role start to
the first complete artifact or stop reason (excluding human approval or queue
wait). A Task is **too long** when it is expected to exceed `T_target`, reaches
`T_checkpoint` without a complete artifact, or needs a second follow-up after
its one permitted immediate handoff. At `T_hard` it is `BLOCKED` and must stop.

A Task is **too wide** when any of these is true:

- it has more than one accountable role or more than one independent concern;
- it needs non-disjoint writers, crosses an unstable shared contract, or has no
  single acceptance artifact;
- its run prompt would exceed 250 words, its handoff would exceed 150 words,
  or the stop condition cannot be stated in one sentence.

Before starting, split a too-long/too-wide Task into dependency-safe slices
with exclusive files, one owner, one acceptance artifact, and one stop
condition. Concurrent branches require frozen scenarios, disjoint resources,
and recorded independence evidence; otherwise price them sequentially. During
a run, emit a checkpoint at `T_checkpoint` or when a metric is crossed:
completed work, evidence, unresolved question, and exactly one next bounded
Task. If setup consumes the useful window, block an unchanged fresh route;
reuse current same-task context only with a material delta, or pre-resolve and
shrink the next Task. At a hard stop, reconcile the live handle and declared
artifact paths before classifying progress, persist the checkpoint, then route
only the remaining work. Never retry or hop models merely to reset the clock.
The Lead hands the slice off; it does not silently extend context or leave the
original Task frozen.

## Skill loading

- **Start with none.** Load skills only when the task brief names them (or the role card’s “load when” trigger matches).
- Paths are relative to this repo: `skills/engineering/…`, `skills/quality/…`, `skills/process/…`, `skills/design/…`.
- One primary skill per task; a second requires a separately recorded unresolved question.
- Product design follows `skills/design/design-router.md`: its required
  `aesthetic` finish lens is review, not a second generator or a second
  accountable Task.
- Do not auto-load every skill because Lead or multi-agent work is happening.

### Skill overrides

Brief triggers override upstream skill “When to Activate” / auto-discovery language. Do not rewrite upstream skill bodies wholesale.

1. **`context-engineering`** — Load **only** when the brief trigger is: create/revise a context packet, bounded investigation, or cross-role synthesis. Never auto-load because Lead, Advisor, multi-agent, or debate work is happening.
2. **`sequential-thinking`** — If host MCP reasoning tools are unavailable: structured written steps in the handoff still satisfy the second-failure skill; do not invent MCP tools.
3. **`problem-solving`** — Exception-only after known root cause or genuine design deadlock; never replace `debugging` for concrete failures.

Advisor / Contradictor default primary skill is `none`. Model tier assignment is orthogonal to skill load.

## Cheap-utility cost tier (pool-mapped)

Prefer the host’s **Tier 0** mapped slug (Codex often maps this to a Luna-class model) for cost-sensitive, high-volume `S0`/`S1` work with an explicit output, bounded evidence or file boundary, and a named stronger owner for synthesis or escalation.

**Default cheap-utility roles / cells:** Investigator; low-risk single-boundary Frontend Builder; eligible temporary support cells (evidence/citation collection, request classification, assumption inventory, stakeholder-lens extraction, dependency/status aggregation, synthetic fixtures, focused test support, failure-log triage).

**Do not** use cheap-utility as the accountable default for Lead, PM, Backend, Frontend/UX contract ownership, Code Reviewer, Test Engineer validation synthesis, Docs Steward governed docs, or Gatekeeper. Escalate Tier 0 → Tier 1 build/validate when evidence conflicts, scope crosses modules, behavior is statefully complex, validation fails, or accessibility/security/privacy/public-contract implications appear. Escalate to Tier 2/3 only under recorded high-risk triggers in [model-routing.md](model-routing.md).

## Functional Integration Owner (FIO)

Each batch names one **Functional Integration Owner**: the role accountable for the integrated behavior after individual tasks land (usually Backend or Frontend Builder for that surface). FIO:

- Owns cross-task seams inside the batch
- Does not replace Code Reviewer risk verification, Test Engineer evidence, or Gatekeeper accept/block
- Surfaces integration gaps in the checkpoint before TE runs
- Does not manage teammates, expand scope, or issue Gatekeeper decisions

## Default batch shape

1. Brief + nature/tier classification
2. Triggered concern method + consult: choose the smallest fitting method, start with one accountable role, and add one decision-changing specialist at a time (per [model-routing.md](model-routing.md)); use the bounded meeting rules in [meeting-policy.md](meeting-policy.md) for material defects, state risks, or cross-role conflicts
3. Conditional acceptance design: PM `user-stories`/`pre-mortem` when triggered + Domain Advisor input → pre-build Test Engineer scenario matrix
4. Human gate when required ([human-gates.md](human-gates.md))
5. Builders (WIP ≤ 2; exclusive files — [concurrency.md](concurrency.md))
6. Freeze the integrated candidate and run declared deterministic checks
7. **Code Reviewer** independently reviews the bounded packet and route without mutating or accepting the candidate
8. **Test Engineer** evidence in a fresh post-integration context when `qa-operating-model.md` requires TE
9. **Gatekeeper** always makes the final accept / revise / block decision
10. Docs Steward if durable docs are in scope

Use acceptance design for user-facing workflows, input parsing/matching, AI
extraction, public contracts, or materially ambiguous acceptance. PM supplies
user outcomes, personas, and acceptance criteria; a Domain Advisor supplies
named-domain meaning only when triggered. Test Engineer freezes an observable
scenario matrix before builders. It is implementation input, not final TE
evidence. For suitable deterministic unit, contract, or component cases,
builder briefs require selective red-green-refactor; do not force E2E-first.

The conditional TE triggers and Reviewer verdict routes live once in
`qa-operating-model.md`. Candidate mutation requires fresh checks and review;
Reviewer is non-terminal and Gatekeeper remains final.

### Finding resolution

Each Reviewer, Test Engineer, or Gatekeeper pass collects all in-scope findings
before issuing its result; Lead does not dispatch fixes mid-pass. `REVISE`
returns the complete finding set to the named owner for one bounded in-scope
Task with exclusive files. This is ordinary Task routing, not a separate
correction admission or human micro-gate. New scope, owner, material risk, or
any independently gated action stops for the applicable human decision.
Cluster findings by demonstrated root cause, preserve or add a failing
regression where feasible, then rebind the candidate and repeat deterministic
checks and fresh Code Reviewer review. Apply the QA route again. Failed
required evidence or `BLOCK` stops; Gatekeeper remains final.

For the full participant, artifact, and PDCA rules, use
[meeting-policy.md](meeting-policy.md). “Test all” means the complete frozen
Batch matrix, not an unbounded repository-wide rerun.

## WIP, rotation, and context economy

Default WIP:

- one `ACTIVE` sprint
- one `ACTIVE` implementation batch and one next `READY` batch
- ≤2 concurrent ordinary tool-using specialists total (including Investigator); plus ≤1 read-only supervisor relay only under `core/concurrency.md`
- one active write task per role; one writer per file
- no reserved “support lane” that bypasses the task list; the narrow supervisor-relay exception remains observational and task-bound

Parallel tasks require satisfied dependencies, stable contracts, disjoint files, own acceptance, and known integration order. Fake parallel is a Lead planning defect.

Do not create standing coordinators, shadows, helpers, or consolidation agents. Every contributor owns a normal task-list item with exclusive deliverable and stop condition. When queueing blocks the critical path, re-sequence or split — optionally use cheap-utility temporary cells under the same WIP cap with one accountable synthesizer.

If a task is too wide for one bounded run, split it into small dependency-safe
Tasks with exclusive files, explicit acceptance, and a stop condition. Hand off
the completed slice with evidence, unresolved questions, and the next bounded
Task. Do not leave an oversized task frozen, silently extend its context, or
restart it without a checkpoint.

Urgent work uses an explicit **expedite batch** after checkpointing the active batch — never silent injection.

## Time budget and semantic status

- Target `T_target` when practical while preserving `T_reserve`
- At `T_checkpoint` → `PARTIAL` with evidence, unresolved question, next bounded step
- At `T_hard` → cancel or split rather than waiting out the provider
- Bounded QA uses the active profile's `T_target`, `T_checkpoint`, `T_hard`,
  and `T_reserve`. A timed-out validation
  records `BLOCKED` evidence and one next action; Lead hands off one smaller
  follow-up Task instead of leaving the batch frozen. It never auto-retries or
  starts Gatekeeper.
- Transport `completed` with empty/malformed/timeout content → `FAILED_TRANSIENT` (not accepted work)

## Adapter note

Runtime wiring (how tasks are spawned, which model pool is used, how approvals are collected) lives under `adapters/`. **Adapter binds runtime** — core policy here stays host-independent.
