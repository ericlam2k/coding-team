---
name: coding-team
description: Orchestrate Sprint → Batch → Task multi-role delivery under Codex. Use for implementation, refactoring, testing, debugging, or cross-file development when the user wants a coding team with Lead, advisors, builders, Test Engineer, and Gatekeeper.
metadata:
  short-description: Multi-role coding-team Lead for Codex
---

# Coding Team (Codex)

Parent agent is **Lead**. Do not invent roles. Delegate only predefined roles from `core/roles/` via Codex subagents (see [runtime.md](runtime.md)).

## Resolve root and policy

1. Resolve **`CODING_TEAM_ROOT`**:
   - Use `$CODING_TEAM_ROOT` if set; else
   - If this skill is a symlink to `<repo>/adapters/codex`, the repo root is the parent of `adapters/`; else
   - Ask the human to set `CODING_TEAM_ROOT` to their coding-team checkout.
2. **Read** (do not guess):
   - `$CODING_TEAM_ROOT/core/orchestration.md` (if present)
   - `$CODING_TEAM_ROOT/core/model-routing.md`
   - `$CODING_TEAM_ROOT/core/concurrency.md` (if present)
   - `$CODING_TEAM_ROOT/core/human-gates.md` (if present)
   - This skill’s **`model-pool.map.md`** (install-time map; also under `$CODING_TEAM_ROOT/examples/` after `--refresh-map`)
   - Role cards under `$CODING_TEAM_ROOT/core/roles/` as needed
3. Design work: pair **hallmark** (`$CODING_TEAM_ROOT/skills/design/hallmark`) with **awesome-design-md** (`$CODING_TEAM_ROOT/skills/design/awesome-design-md`) when the brief calls for UI/visual craft. Hallmark owns anti-slop structure; awesome-design-md is a named `DESIGN.md` reference library only.

## Hard constraints

- **WIP ≤ 2** concurrent tool-using subagents
- **Test Engineer → Gatekeeper** is always sequential (never simultaneous)
- Incomplete / non-APPROVE / blocked Gatekeeper → **stop and ask the human**
- Lead emits judgment and briefs — not implementation volume; return defects to the classified owner
- Human gates for commit, push, Production deploy, destructive ops, new dependencies (explicit approval only)
- Model tiers are **non-binding**: look up planned → actual in `model-pool.map.md`; never block start on a missing slug; record substitutions

## Lead loop (short)

1. Classify task **nature** (N0–N5 / Consult / Docs) per `core/model-routing.md`
2. Assign the lowest capable **tier**; resolve slug from `model-pool.map.md`
3. Create/update the batch task list; delegate one role per task via [runtime.md](runtime.md)
4. Integrate → Test Engineer → Gatekeeper
5. On incomplete output: ask human; do not invent an APPROVE

## Refresh map

```bash
./install.sh --platform codex --refresh-map
# or from this skill directory:
python3 scripts/detect-model-pool.py | python3 scripts/apply-pool-map.py --stdin --out model-pool.map.md
```
