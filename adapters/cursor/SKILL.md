---
name: coding-team
description: Platform-independent Sprint → Batch → Task coding team. Use for multi-role delivery under Cursor. Lead classifies nature, maps tiers from model-pool.map.md, delegates via Task agents.
---

# Coding Team (Cursor)

Parent Agent is **Lead**. Never spawn a Lead subagent.

## Resolve root

1. Set `CODING_TEAM_ROOT` to this repo checkout, or resolve as parent of `adapters/cursor`.
2. Read `$CODING_TEAM_ROOT/core/orchestration.md`, `model-routing.md`, `concurrency.md`, `human-gates.md`.
3. Read install-approved `model-pool.map.md` next to this skill (or under `$CODING_TEAM_ROOT/adapters/cursor/`).
4. Delegate via Cursor `Task` to role cards in `$CODING_TEAM_ROOT/core/roles/`.

## Hard constraints

- WIP ≤ 2; TE → Gatekeeper sequential
- Incomplete / non-APPROVE → stop for human
- Oversized or timed-out work → split into a bounded Task and hand off the
  checkpoint; do not leave it frozen or silently extend the run.
- Lead cost discipline — briefs, not implementation code
- Optional addons default OFF; use only addons that exist in the active checkout
- When `qa_required=true` or `qa_mode=bounded`, Test Engineer runs the
  QA evidence validator before Gatekeeper. Bounded passes use a 120-second
  target / 240-second hard stop; timeout returns `BLOCKED` without auto-retry.

See `$CODING_TEAM_ROOT/adapters/cursor/runtime.md`.
