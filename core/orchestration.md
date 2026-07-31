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
| PDCA + experiments + performance log | Kaizen | Root cause + named PIC → plan → observe → re-evaluate → **consolidate** (bake or close) |
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
- Routes defects to the classified owner as corrected briefs
- Does **not** implement product code or invent new roles

Incomplete or non-APPROVE outputs → **stop for human** ([human-gates.md](human-gates.md)).

### Lead cost discipline — emit judgment, not volume

The Lead runs the most expensive context in the system. Its output is classification, briefs, routing, verdicts on evidence, and short reports — never implementation code.

- **No typing lane:** a code block longer than an interface signature or a few illustrative lines is an undelegated spec — stop and delegate it to the owning builder.
- **Defects go back as briefs:** never hand-fix a builder's bug. Classify the failure and send a **corrected brief** to that owner.
- **Reason once, then hand off:** capture architecture/hypothesis thinking in the brief; do not re-derive it across turns.
- **Spec-readiness test:** a run prompt you cannot finish writing (objective, files, interfaces, constraints, verification) means the decision is not made yet. That is Lead/Advisor work — never delegate the ambiguity to a cheaper tier.

## Canonical role IDs

Use only these IDs (see `roles/`):

| ID | Role |
|---|---|
| `lead` | Lead |
| `product-manager` | Product Manager |
| `advisor` | Advisor (technical, pre-build) |
| `contradictor` | Contradictor |
| `domain-advisor` | Domain Expert **template** → instances `{domain}-advisor` (see [domain-advisors.md](domain-advisors.md)) |
| `investigator` | Investigator |
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

## Skill loading

- **Start with none.** Load skills only when the task brief names them (or the role card’s “load when” trigger matches).
- Paths are relative to this repo: `skills/engineering/…`, `skills/quality/…`, `skills/process/…`, `skills/design/…`.
- One primary skill per task; a second requires a separately recorded unresolved question.
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

**Do not** use cheap-utility as the accountable default for Lead, PM, Backend, Frontend/UX contract ownership, Test Engineer validation synthesis, Docs Steward governed docs, or Gatekeeper. Escalate Tier 0 → Tier 1 build/validate when evidence conflicts, scope crosses modules, behavior is statefully complex, validation fails, or accessibility/security/privacy/public-contract implications appear. Escalate to Tier 2/3 only under recorded high-risk triggers in [model-routing.md](model-routing.md).

## Functional Integration Owner (FIO)

Each batch names one **Functional Integration Owner**: the role accountable for the integrated behavior after individual tasks land (usually Backend or Frontend Builder for that surface). FIO:

- Owns cross-task seams inside the batch
- Does not replace Test Engineer evidence or Gatekeeper accept/block
- Surfaces integration gaps in the checkpoint before TE runs
- Does not manage teammates, expand scope, or issue Gatekeeper decisions

## Default batch shape

1. Brief + nature/tier classification  
2. Optional Investigator / PM / Advisor / Contradictor (per [model-routing.md](model-routing.md))  
3. Human gate when required ([human-gates.md](human-gates.md))  
4. Builders (WIP ≤ 2; exclusive files — [concurrency.md](concurrency.md))  
5. **Test Engineer** evidence  
6. **Gatekeeper** accept / revise / block  
7. Docs Steward if durable docs are in scope  

## WIP, rotation, and context economy

Default WIP:

- one `ACTIVE` sprint
- one `ACTIVE` implementation batch and one next `READY` batch
- ≤2 concurrent tool-using specialists total (including Investigator)
- one active write task per role; one writer per file
- no reserved “support lane” that bypasses the task list

Parallel tasks require satisfied dependencies, stable contracts, disjoint files, own acceptance, and known integration order. Fake parallel is a Lead planning defect.

Do not create standing coordinators, shadows, helpers, or consolidation agents. Every contributor owns a normal task-list item with exclusive deliverable and stop condition. When queueing blocks the critical path, re-sequence or split — optionally use cheap-utility temporary cells under the same WIP cap with one accountable synthesizer.

Urgent work uses an explicit **expedite batch** after checkpointing the active batch — never silent injection.

## Time budget and semantic status

- Target ~120s when practical
- At ~180s → `PARTIAL` with evidence, unresolved question, next bounded step
- At ~240s → cancel or split rather than waiting out the provider
- Transport `completed` with empty/malformed/timeout content → `FAILED_TRANSIENT` (not accepted work)

## Adapter note

Runtime wiring (how tasks are spawned, which model pool is used, how approvals are collected) lives under `adapters/`. **Adapter binds runtime** — core policy here stays host-independent.
