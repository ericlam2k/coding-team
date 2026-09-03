---
name: coding-team
description: Platform-independent Sprint → Batch → Task coding team for Cline. Lead classifies nature, uses approved model-pool.map.md, delegates to predefined roles only.
---

# Coding Team (Cline)

Lead teammate orchestrates. Do not invent roles.

## Resolve root

1. Set `CODING_TEAM_ROOT` to this checkout.
2. Read `$CODING_TEAM_ROOT/core/*.md` and approved `model-pool.map.md`.
3. Delegate only canonical roles under `$CODING_TEAM_ROOT/core/roles/`.

## Hard constraints

Same as core: WIP ≤ 2 ordinary tool-using teammates plus at most one optional
read-only, non-authoritative supervisor relay (maximum child lanes = 3 only
when admitted; never a third ordinary lane); Code Reviewer → conditional Test
Engineer → Gatekeeper remains sequential. Human gates, Lead cost discipline,
and addons OFF unless enabled also apply. Oversized or timed-out work is split
into a bounded Task and handed off with its checkpoint; it is not left frozen.
When `qa_required=true` or `qa_mode=bounded`, TE runs the QA evidence validator
before GK. Bounded passes use a 120-second target / 240-second hard stop;
timeout returns `BLOCKED` without auto-retry.

See `adapters/cline/runtime.md`.
