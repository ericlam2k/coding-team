# Core (platform-agnostic)

Host-independent coding-team policy. Adapters under `adapters/` bind this core to a runtime (**adapter binds runtime** — core does not favor any IDE or agent host).

## Index

| Path | Purpose |
|---|---|
| [orchestration.md](orchestration.md) | Sprint → Batch → Task; Lead authority; role IDs; context caps; skill loading; FIO |
| [model-routing.md](model-routing.md) | Abstract tiers 0 / 1build / 1validate / 2 / 3 + nature table (no host slugs) |
| [meeting-policy.md](meeting-policy.md) | Lean concern meeting, PM/domain → TE scenario design, PDCA correlation, and no-mutation correction loop |
| [qa-operating-model.md](qa-operating-model.md) | Traditional QA flow, conditional test layers, evidence packet, and promotion gates |
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
| [templates/review-decision.md](templates/review-decision.md) | Gatekeeper decision |
| [templates/final-report.md](templates/final-report.md) | Sprint/batch close report |
| [templates/performance-entry.md](templates/performance-entry.md) | Tier 2/3 / substitution log |

## Skills layout (this repo)

| Tree | Contents |
|---|---|
| `skills/engineering/` | Backend, frontend, frameworks, performance, styling, data, devops |
| `skills/quality/` | Testing, review, debugging, problem-solving, sequential thinking |
| `skills/process/` | Context engineering, docs seeker, PM execution |
| `skills/design/` | Hallmark + awesome-design-md (paired), ui-ux-pro-max, aesthetic, frontend-design |

## Install note

Map abstract tiers to your host’s model pool in install-time `model-pool.map.md`. Lead classifies **nature**, assigns a **tier**, then looks up the mapped slug.
