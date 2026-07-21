# Skills

Start every task with **no** specialist skill (`none`). Load **one** primary skill only when the brief names its trigger. A second skill needs a separate unresolved question.

## Bundled layout

```text
skills/
  engineering/   backend-development, frontend-development, databases, devops,
                 web-frameworks, react-next-performance, ui-styling
  quality/       debugging (+ sub-skills), code-review, web-testing,
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
| Investigator | `context-engineering` for bounded investigation |
| Backend Engineer | `backend-development`, `databases`, `debugging`, `web-frameworks` |
| Frontend/UX Lead | `hallmark`, `awesome-design-md` (via index), `frontend-design`, `ui-ux-pro-max` |
| Frontend Builder | `frontend-development`, `ui-styling`, `web-frameworks`, `hallmark` when assigned, `react-next-performance` |
| Test Engineer | `web-testing`, `debugging` |
| Docs Steward | `docs-seeker` |
| Gatekeeper | `code-review` (read-only) |

## Debugging family

`skills/quality/debugging/` counts as one primary with exactly one matching sub-skill initially (`systematic-debugging`, `root-cause-tracing`, `defense-in-depth`, `verification-before-completion`). Second failure may add `sequential-thinking`. Known-root-cause design deadlocks use `problem-solving`.

## Not bundled (add per project)

Market-research / product-discovery packs, payment providers, shop frameworks, 3D, etc. Keep the framework lean.
