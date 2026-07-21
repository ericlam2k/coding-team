# Definitions

Shared vocabulary for coding-team. Use these terms in briefs, handoffs, and docs so humans and agents mean the same thing.

## Operating model

| Term | Definition |
|---|---|
| **Sprint** | A coordination window with one measurable outcome, governing specs, non-goals, human gates, and ordered batches. Prefer one active sprint. |
| **Batch** | The dependency-safe unit of context, integration, validation, and Gatekeeper review. Normal size: 2–5 related tasks. States: `PROPOSED → READY → ACTIVE → VALIDATING → REVIEW → COMPLETE` (also `PAUSED` / `BLOCKED` / `CANCELLED`). |
| **Task** | One atomic deliverable with one canonical owner, exclusive file ownership, dependencies, stop condition, one primary skill or `none`, and an owner self-check. |
| **Lead** | The parent agent/session that classifies nature, assigns tiers, creates the task list, delegates, integrates, and enforces gates. Never spawn Lead as a subagent. |
| **Functional Integration Owner** | An assignment (not a new role) naming which existing role owns the batch’s shared contract and integration order before independent validation. |
| **WIP ≤ 2** | At most two concurrent tool-using specialist runs. Accelerate by smaller queued work and proven-disjoint parallels — never by raising the cap. |
| **Handoff** | ≤150-word return packet from a specialist: status, evidence paths, unresolved questions, next owner. |
| **Checkpoint** | ≤300-word batch state snapshot used after pause, context shrink, or Gatekeeper acceptance. |
| **Run prompt** | ≤250-word delegation prompt projected from the task brief. The full template is never the run prompt. |

## Nature (N0–N5)

Lead classifies every task before delegation:

| Nature | Meaning |
|---|---|
| **N0** | Map / fact lookup (read-only investigation) |
| **N1** | Bounded build with clear acceptance |
| **N2** | Contract, UX, or multi-owner integration |
| **N3** | Validate, reproduce, or classify failure |
| **N4** | Independent technical decision |
| **N5** | High-risk / irreversible — human gate before eco build |
| **Consult** | Product (or domain) advice without implementation |
| **Docs** | Durable documentation only |

Full route table: [core/model-routing.md](../core/model-routing.md).

## Tiers (abstract)

Tiers describe **capability intent**, not a fixed vendor slug:

| Tier | Intent |
|---|---|
| **0** | Cheap utility (lookup, light docs) |
| **1 build** | Eco implementer |
| **1 validate** | Careful validator / Test Engineer |
| **2** | Premium plan, debate, Gatekeeper |
| **3** | Max-risk judgment (N5 / Adv↔Con deadlock) |

Concrete slugs appear only in install-time `model-pool.map.md`. See [model-pool-mapping.md](model-pool-mapping.md).

## Decisions & outcomes

| Term | Definition |
|---|---|
| **Advisor** | Pre-build: what should we do? |
| **Contradictor** | Pre-build: why might this be wrong? Serial debate with Advisor when required. |
| **Gatekeeper** | Post-build: `APPROVE` / `APPROVE_WITH_NOTES` / `REVISE` / `BLOCK` after Test Engineer evidence. |
| **Human gate** | Explicit human approval for irreversible or ambiguous risk. Silence is never approval. |
| **PARTIAL** | Timed/incomplete work with evidence + next bounded step — not success. |
| **FAILED_TRANSIENT** | Transport/runtime failure; shrink or retry per policy — do not invent success. |

## Scope & validation levels

| Code | Meaning |
|---|---|
| **S0** | Consult / evidence only — no writes |
| **S1** | Default: one deliverable, explicit read/write boundary |
| **S2** | Cross-module / high-risk — recorded trigger required |
| **V0–V3** | Validation depth from smoke to release-grade (set at batch READY) |

## Design pairing

| Term | Definition |
|---|---|
| **Hallmark** | Anti-AI-slop design skill; primary design authority for greenfield / redesign when assigned. |
| **awesome-design-md** | Named `DESIGN.md` reference library. Read via [skills/design/design-md-index.md](../skills/design/design-md-index.md): at most one primary + one comparison; principles only — never clone branding. |

## What coding-team is not

- Not a product backlog tool or Jira replacement
- Not automatic permission to commit, push, deploy, or rotate secrets
- Not a guarantee of a specific model brand — only tier intent + pool map
- Not Career Intelligence–specific policy (this framework is generic)
