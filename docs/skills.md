# Skills

Start every task with **no** specialist skill (`none`). Load **one** primary skill only when the brief names its trigger. A second skill needs a separate unresolved question.

Concern methods are not skills. Choose the lean concern method first; load an
existing skill only when its named trigger remains necessary. Never load a
skill merely because a brainstorm, debate, or `5 Whys` occurs.

## Bundled layout

```text
skills/
  engineering/   backend-development, frontend-development, databases, devops,
                 web-frameworks, react-next-performance, ui-styling
  quality/       debugging (+ sub-skills), code-review, web-testing,
                 qa-evidence-enforcement,
                 sequential-thinking, problem-solving
  process/       context-engineering, pm-execution, docs-seeker
  design/        hallmark, awesome-design-md, frontend-design, aesthetic,
                 ui-ux-pro-max, design-md-index.md
```

## Design pairing (preferred)

1. **Hallmark** — anti-AI-slop structure and visual discipline for greenfield / redesign / audit.
2. **awesome-design-md** — named brand `DESIGN.md` references via [`skills/design/design-md-index.md`](../skills/design/design-md-index.md).
3. Rules: open the index first; at most **one primary + one comparison**; extract **principles only**; never clone branding, fonts, or logos; project tokens/specs still win when present.
4. When both Hallmark and `frontend-design` / `aesthetic` / `ui-ux-pro-max` could apply, **Hallmark wins** unless the brief names a narrower trigger.

## Role → skill coverage

| Role | Typical skills (on trigger) |
|---|---|
| Lead | `context-engineering` (packets only), `code-review` (handoff check) |
| Product Manager | `pm-execution`, `context-engineering` |
| Advisor / Contradictor | usually `none` (+ packet if assigned) |
| Domain Advisor | supplied domain evidence; `context-engineering` only for a named multi-source packet; one project-domain skill only when named |
| Investigator | `context-engineering` for bounded investigation |
| System Architect | `engineering/system-architecture` only for the cross-layer/shared-contract trigger; add another named skill only for a distinct unresolved question |
| Backend Engineer | `backend-development`, `databases`, `debugging`, `web-frameworks` |
| Frontend/UX Lead | `hallmark`, `awesome-design-md` (via index), `frontend-design`, `ui-ux-pro-max` |
| Frontend Builder | `frontend-development`, `ui-styling`, `web-frameworks`, `hallmark` when assigned, `react-next-performance` |
| Test Engineer | `web-testing`, `qa-evidence-enforcement` (bounded evidence only), `debugging`, `doc-reader-test` (explicit-only), `pm-execution/test-scenarios` (pre-build only) |
| Docs Steward | `docs-seeker`, `stakeholder-update` (explicit-only), `artifact-theme` (non-product artifacts only) |
| Gatekeeper | `code-review` (read-only) |

## Pre-build test-case development chain

For user-facing workflows, input parsing/matching, AI extraction, public
contracts, or materially ambiguous acceptance:

1. Product Manager uses `pm-execution/user-stories` when the user outcome or
   acceptance is unclear.
2. Product Manager uses `pm-execution/pre-mortem` when failure, replay, stale
   state, or fix–trial-loop risk is material. These are sequential conditional
   skills, not a default pair.
3. A named Domain Advisor supplies domain workflow, exception, fairness, and
   recovery cases when triggered; it has no default specialist skill.
4. Test Engineer uses
   `skills/process/pm-execution/test-scenarios/` before builders to freeze the
   user-observable matrix. This is design input only.
5. Final Test Engineer execution uses `skills/quality/web-testing/` in a fresh
   context; `skills/quality/debugging/` is added only when failures require
   classification or root-cause tracing.
   For qa_required=true or qa_mode=bounded, run
   `skills/quality/qa-evidence-enforcement/` after execution. Bounded passes
   use the 120-second target / 240-second hard stop and record `BLOCKED` on
   timeout; they do not auto-retry.

The complete no-mutation validation, correlation, and PIC routing policy is in
[`core/meeting-policy.md`](../core/meeting-policy.md).

Layer selection and QA evidence requirements are governed by
[`core/qa-operating-model.md`](../core/qa-operating-model.md). The model adds
no skills or automatic role calls; it only activates the named skill when its
trigger applies.

## Debugging family

`skills/quality/debugging/` counts as one primary with exactly one matching sub-skill initially (`systematic-debugging`, `root-cause-tracing`, `defense-in-depth`, `verification-before-completion`). Second failure may add `sequential-thinking`. Known-root-cause design deadlocks use `problem-solving`.

PM Lean is default OFF and explicit-only: use at most one PM Lean skill per
Product Manager task; it adds no routing, agents, or approval authority.

## Not bundled (add per project)

Market-research / product-discovery packs, payment providers, shop frameworks, 3D, etc. Keep the framework lean.
