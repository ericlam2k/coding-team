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
| **WIP ≤ 2 ordinary + ≤1 supervisor relay** | At most two concurrent ordinary tool-using specialist runs, plus one optional read-only, non-authoritative supervisor relay. Total child lanes may reach 3 only when that relay is admitted; never start a third ordinary run. |
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
| **Domain Advisor** | Specialty consult peer. Template `domain-advisor` → instance `{domain}-advisor` / display `[Domain]-Advisor` (e.g. Talent-Advisor, Strategic-Advisor). Lead asks for domain when unclear. Not under PM or technical Advisor. |
| **Advisor** | Pre-build: what should we do *technically*? |
| **Contradictor** | Pre-build: why might this be wrong? Serial debate with Advisor when required. |
| **Code Reviewer** | Independent post-build diff/risk review; routes conditional Test Engineer evidence before Gatekeeper and never accepts. |
| **Monitor Agent** | Optional bounded read-only supervisor relay under the frozen contract; reports one create-once artifact result and never controls work or accepts. |
| **Gatekeeper** | Final post-build authority: `APPROVE` / `APPROVE_WITH_NOTES` / `REVISE` / `BLOCK` after the routed evidence, including Test Engineer evidence when required. |
| **Human gate** | Explicit human approval for irreversible or ambiguous risk. Silence is never approval. |
| **Lead cost discipline** | Lead emits judgment/briefs only — no implementation typing lane; defects return as corrected briefs; spec-readiness before dispatch. |
| **Spec-readiness** | A ≤250-word run prompt with objective, files, interfaces, constraints, and verification — if you cannot finish it, do not delegate yet. |
| **Cheap-utility / Luna-class** | Pool **Tier 0** after install (often `gpt-5.6-luna` on Codex). For Investigator, low-risk FE Builder, eligible support cells — not for Lead/PM/Backend/UX/TE/Docs/Gatekeeper defaults. |
| **PARTIAL** | Timed/incomplete work with evidence + next bounded step — not success. |
| **FAILED_TRANSIENT** | Transport/runtime failure; shrink or retry per policy — do not invent success. |
| **Alias normalization** | Map Explorer/Inspector/Reviewer labels to canonical roles; domain labels → `{domain}-advisor` — never invent a new role *family*. |

## Scope & validation levels

| Code | Meaning |
|---|---|
| **S0** | Consult / evidence only — no writes |
| **S1** | Default: one deliverable, explicit read/write boundary |
| **S2** | Cross-module / high-risk — recorded trigger required |
| **V0–V3** | Validation depth from smoke to release-grade (set at batch READY) |

## Product design routing

| Term | Definition |
|---|---|
| **Design router** | [`skills/design/design-router.md`](../skills/design/design-router.md) selects one primary generator by surface scenario, zero or one reference, and the required non-authoritative aesthetic finish lens. |
| **anti-ui-slop** | Primary for operational UI, refinement, or usability audit; load exactly one playbook. |
| **Hallmark** | Primary generator for `brand_web` when assigned. |
| **awesome-design-md** | Optional named `DESIGN.md` reference for `brand_web`; principles only — never clone branding. |
| **Aesthetic review** | Required finish lens for material design work; it reviews craft but never replaces product authority or acceptance. |

## Lead cost discipline

Lead output is classification, briefs, routing, and short verdicts — **not** implementation volume. A run prompt that cannot state objective, files, interfaces, constraints, and verification fails the **spec-readiness test** and must not be delegated to a cheaper tier.

## Cheap-utility / Luna-class tier

Host Tier **0** (often GPT Luna on Codex) is for Investigator, low-risk Frontend Builder, and eligible support cells. It is not the accountable default for Lead, PM, Backend, Frontend/UX Lead, Test Engineer synthesis, Docs Steward, or Gatekeeper.

## Skill overrides

Upstream skill “When to Activate” language does not auto-load inside coding-team. `context-engineering` only on packet/investigation/synthesis triggers; `problem-solving` never replaces `debugging` for concrete failures.

## What coding-team is not

- Not a product backlog tool or Jira replacement
- Not automatic permission to commit, push, deploy, or rotate secrets
- Not a guarantee of a specific model brand — only tier intent + pool map
- Not product-specific policy for any one application
