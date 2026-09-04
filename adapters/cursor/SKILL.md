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
- Incomplete work returns to Lead for correction or rerouting
- Lead writes briefs and routes handoffs, never implementation code
- PM Lean addon default OFF; enable it only for an explicit PM task

See `$CODING_TEAM_ROOT/adapters/cursor/runtime.md`.
