---
name: coding-team
description: Platform-independent Sprint → Batch → Task coding team for OpenCode. Lead delegates predefined builders, Code Reviewer, Test Engineer, and Gatekeeper only.
---

# Coding Team (OpenCode)

Lead teammate orchestrates. Do not invent roles.

## Resolve root

1. Set `CODING_TEAM_ROOT` to this checkout.
2. Read `$CODING_TEAM_ROOT/core/*.md` and the approved `adapters/opencode/model-pool.map.md` when configured.
3. Delegate only canonical roles under `$CODING_TEAM_ROOT/core/roles/`.

## Hard constraints

Same as core: WIP ≤ 2, canonical `code-reviewer` → QA route → GK under
`core/qa-operating-model.md`, human gates, Lead cost discipline,
addons OFF unless enabled. Oversized or timed-out work is split into a bounded
Task and handed off with its checkpoint; it is not left frozen. When
`qa_required=true` or `qa_mode=bounded`, TE runs the QA evidence validator
before GK. Bounded passes use a 120-second target / 240-second hard stop;
timeout returns `BLOCKED` without auto-retry.

## Trial scope (lab)

Private lab trial on `adapter/opencode-wysy-lab`. Reuse `core/` read-only.
No `core/` changes, no push/merge to `main`, no public sync without a separate
human approval. Evidence = hermetic OpenCode run receipts at a recorded SHA.

See `adapters/opencode/runtime.md` and `adapters/opencode/AGENTS.md`.
