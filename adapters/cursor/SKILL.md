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

- WIP ≤ 2 ordinary tool-using Tasks, plus at most one optional read-only,
  non-authoritative supervisor relay (maximum child lanes = 3 only when
  admitted; never a third ordinary lane)
- Code Reviewer → conditional Test Engineer → Gatekeeper sequential
- Incomplete / non-APPROVE → stop for human
- Oversized or timed-out work → split into a bounded Task and hand off the
  checkpoint; do not leave it frozen or silently extend the run.
- Lead cost discipline — briefs, not implementation code
- PM Lean addon default OFF; enable it only for an explicit PM task
- When `qa_required=true` or `qa_mode=bounded`, Test Engineer runs the
  QA evidence validator before Gatekeeper. Bounded passes use a 120-second
  target / 240-second hard stop; timeout returns `BLOCKED` without auto-retry.
- After a hard stop, verify the live handle or terminal state and inspect the
  declared artifact paths. Record `COMPLETE`, `PARTIAL`, or `NO_PROGRESS`,
  preserve usable work, and price one materially changed smaller route under
  `core/adaptive-timing.md`; never repeat the stopped route or hop models.

See `$CODING_TEAM_ROOT/adapters/cursor/runtime.md`.
