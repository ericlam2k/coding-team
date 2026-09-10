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

Same as core: WIP ≤ 2 ordinary teammates, one accountable owner per task, and
no supervisor lane. Code Reviewer, Test Engineer, and Gatekeeper are
independent risk triggers. Human gates and addons OFF unless enabled apply.

See `adapters/cline/runtime.md`.
