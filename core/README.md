# Core (platform-agnostic)

Host-independent coding-team policy. Adapters under `adapters/` bind this core to a runtime (**adapter binds runtime** — core does not favor any IDE or agent host).

## Index

| Path | Purpose |
|---|---|
| [orchestration.md](orchestration.md) | Sprint → Batch → Task; Lead authority; role IDs; context caps; skill loading; FIO |
| [model-routing.md](model-routing.md) | Abstract tiers 0 / 1build / 1validate / 2 / 3 + nature table (no host slugs) |
| [meeting-policy.md](meeting-policy.md) | Lead-owned concern and new-idea brainstorm meetings, PM/domain → TE scenario design, PDCA correlation, and no-mutation correction loop |
| [learning-and-distillation.md](learning-and-distillation.md) | Evidence-linked learning capture, bounded distillation, validation, and governed promotion |
| [qa-operating-model.md](qa-operating-model.md) | Hybrid Normal/Risky QA flow, selected layers, evidence, and promotion gates |
| [../docs/archive/qa-operating-model-pre-hybrid-29311de.md](../docs/archive/qa-operating-model-pre-hybrid-29311de.md) | Archived pre-hybrid QA policy; reference only |
| [domain-advisors.md](domain-advisors.md) | Domain Expert → `[Domain]-Advisor` / `{domain}-advisor` |
| [concurrency.md](concurrency.md) | WIP ≤ 2; TE → Gatekeeper sequential; parallel rules |
| [human-gates.md](human-gates.md) | Approval before implement/ops; incomplete → stop; silence ≠ approval |
| [roles/](roles/) | Canonical role cards |
| [templates/](templates/) | Sprint / batch / task / handoff / checkpoint / review / report / perf |

## Roles

| File | Role ID |
|---|---|
| [roles/lead.md](roles/lead.md) | `lead` |
| [roles/product-manager.md](roles/product-manager.md) | `product-manager` |
| [roles/advisor.md](roles/advisor.md) | `advisor` |
| [roles/contradictor.md](roles/contradictor.md) | `contradictor` |
| [roles/domain-advisor.md](roles/domain-advisor.md) | `domain-advisor` → `{domain}-advisor` |
| [roles/investigator.md](roles/investigator.md) | `investigator` |
| [roles/system-architect.md](roles/system-architect.md) | `system-architect` |
| [roles/backend-engineer.md](roles/backend-engineer.md) | `backend-engineer` |
| [roles/frontend-ux-lead.md](roles/frontend-ux-lead.md) | `frontend-ux-lead` |
| [roles/frontend-builder.md](roles/frontend-builder.md) | `frontend-builder` |
| [roles/test-engineer.md](roles/test-engineer.md) | `test-engineer` |
| [roles/docs-steward.md](roles/docs-steward.md) | `docs-steward` |
| [roles/gatekeeper.md](roles/gatekeeper.md) | `gatekeeper` |

## Templates

| File | Use |
|---|---|
| [templates/sprint-brief.md](templates/sprint-brief.md) | Sprint (≤600w) |
| [templates/batch-brief.md](templates/batch-brief.md) | Batch (≤450w) |
| [templates/task-brief.md](templates/task-brief.md) | Task + run prompt (≤250w) |
| [templates/handoff.md](templates/handoff.md) | Role handoff (≤150w) |
| [templates/batch-checkpoint.md](templates/batch-checkpoint.md) | Batch checkpoint (≤300w) |
| [templates/qa-evidence.json](templates/qa-evidence.json) | Machine-readable QA evidence and promotion manifest |
| [templates/review-decision.md](templates/review-decision.md) | Gatekeeper decision |
| [templates/final-report.md](templates/final-report.md) | Sprint/batch close report |
| [templates/performance-entry.md](templates/performance-entry.md) | Tier 2/3 / substitution log |
| [templates/learning-entry.md](templates/learning-entry.md) | Learning signal and distillation disposition |
| [templates/experiment-entry.md](templates/experiment-entry.md) | Bounded `EXP-*` / PDCA hypothesis and human decision |
| [templates/distillation-entry.md](templates/distillation-entry.md) | Fallback/project lesson and governed promotion |
| [templates/architecture-contract.md](templates/architecture-contract.md) | Named architecture contract before allocation |
| [templates/discovery-brainstorm-meeting.md](templates/discovery-brainstorm-meeting.md) | Lead-owned product-trio discovery packet before PRD/solution selection |

## Skills layout (this repo)

| Tree | Contents |
|---|---|
| `skills/engineering/` | Backend, frontend, system architecture, frameworks, performance, styling, data, devops |
| `skills/quality/` | Testing, review, debugging, bounded QA evidence, problem-solving, sequential thinking |
| `skills/process/` | Context engineering, docs seeker, PM execution |
| `skills/design/` | Hallmark + awesome-design-md (paired), ui-ux-pro-max, aesthetic, frontend-design |

## Install note

Map abstract tiers to your host’s model pool in install-time `model-pool.map.md`. Lead classifies **nature**, assigns a **tier**, then looks up the mapped slug.
