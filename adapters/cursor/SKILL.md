---
name: coding-team
description: Lean Input → Process → Handoff coding team for Cursor.
---

# Coding Team (Cursor)

Parent Agent is **Lead**. Never spawn a Lead subagent.

## Resolve root

1. Set `CODING_TEAM_ROOT` to this repo checkout, or resolve as parent of `adapters/cursor`.
2. Read `$CODING_TEAM_ROOT/core/orchestration.md`, `model-routing.md`, `concurrency.md`, `human-gates.md`.
3. Read install-approved `model-pool.map.md` next to this skill (or under `$CODING_TEAM_ROOT/adapters/cursor/`).
4. Delegate via Cursor `Task` to role cards in `$CODING_TEAM_ROOT/core/roles/`.

## Hard constraints

- WIP ≤ 2 ordinary tool-using Tasks; Lead owns status and there is no supervisor
  lane
- Code Reviewer, Test Engineer, and Gatekeeper are independent risk triggers
- If a named UX or architecture contract was used, that owner reviews the built
  result before Gatekeeper; small patches skip that bounce; high risk does not
  skip the contract owner
- Built-vs-contract inspect uses `frontend-ux-lead:inspect` or
  `system-architect:inspect` (cheap slug). Do not inherit GLM/Sol/Fable for
  browser or HTTP tool loops
- Gatekeeper writes `review-decision.md` from the origin verdict on the
  cheapest capable slug; do not remake the call. `gatekeeper:small` is
  unchanged
- Incomplete work returns to Lead for correction or rerouting
- Lead writes briefs and routes handoffs, never implementation code
- PM Lean addon default OFF; enable it only for an explicit PM task

See `$CODING_TEAM_ROOT/adapters/cursor/runtime.md`.
