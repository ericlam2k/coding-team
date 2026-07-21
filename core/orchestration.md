# Orchestration

Platform-agnostic coding-team flow. An **adapter** binds this core to a specific runtime; do not treat any IDE or agent host as the source of policy.

## Hierarchy

```text
Sprint  →  Batch  →  Task
```

| Level | Owns | Typical artifact |
|---|---|---|
| **Sprint** | Outcome theme, batch order, success criteria | `templates/sprint-brief.md` (≤ **600** words) |
| **Batch** | Integrated deliverable, owned files, validation plan | `templates/batch-brief.md` (≤ **450** words) |
| **Task** | Single role, exclusive scope, one handoff | `templates/task-brief.md` + run prompt (≤ **250** words) |

## Lead authority

The **Lead** (parent orchestrator) is the only role that:

- Classifies **nature** (N0–N5 / Consult / Docs) and assigns **model tier**
- Opens/closes batches, admits tasks, and enforces WIP / gates
- Resolves Advisor vs Contradictor debates
- Routes defects to the classified owner as corrected briefs (judgment, not volume)
- Does **not** implement product code or invent new roles

Incomplete or non-APPROVE outputs → **stop for human** ([human-gates.md](human-gates.md)).

## Canonical role IDs

Use only these IDs (see `roles/`):

| ID | Role |
|---|---|
| `lead` | Lead |
| `product-manager` | Product Manager |
| `advisor` | Advisor |
| `contradictor` | Contradictor |
| `investigator` | Investigator |
| `backend-engineer` | Backend Engineer |
| `frontend-ux-lead` | Frontend UX Lead |
| `frontend-builder` | Frontend Builder |
| `test-engineer` | Test Engineer |
| `docs-steward` | Docs Steward |
| `gatekeeper` | Gatekeeper |

Never invent roles. Domain specialists belong in the product install, not in core.

## Context caps (hard)

| Artifact | Max words |
|---|---|
| Sprint brief | **600** |
| Batch brief | **450** |
| Task run prompt | **250** |
| Handoff | **150** |
| Batch checkpoint | **300** |

Prefer path/line evidence pointers over pasted dumps. Shrink the packet before escalating tier.

## Skill loading

- **Start with none.** Load skills only when the task brief names them (or the role card’s “load when” trigger matches).
- Paths are relative to this repo: `skills/engineering/…`, `skills/quality/…`, `skills/process/…`, `skills/design/…`.
- `skills/process/context-engineering/` only when the brief names a context packet, bounded investigation, or cross-role synthesis trigger.
- Do not auto-load every skill because Lead or multi-agent work is happening.

## Functional Integration Owner (FIO)

Each batch names one **Functional Integration Owner**: the role accountable for the integrated behavior after individual tasks land (usually Backend or Frontend Builder for that surface). FIO:

- Owns cross-task seams inside the batch
- Does not replace Test Engineer evidence or Gatekeeper accept/block
- Surfaces integration gaps in the checkpoint before TE runs

## Default batch shape

1. Brief + nature/tier classification  
2. Optional Investigator / PM / Advisor / Contradictor (per [model-routing.md](model-routing.md))  
3. Human gate when required ([human-gates.md](human-gates.md))  
4. Builders (WIP ≤ 2; exclusive files — [concurrency.md](concurrency.md))  
5. **Test Engineer** evidence  
6. **Gatekeeper** accept / revise / block  
7. Docs Steward if durable docs are in scope  

## Adapter note

Runtime wiring (how tasks are spawned, which model pool is used, how approvals are collected) lives under `adapters/`. **Adapter binds runtime** — core policy here stays host-independent.
