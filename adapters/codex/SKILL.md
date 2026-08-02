---
name: coding-team
description: Orchestrate Sprint → Batch → Task multi-role delivery under Codex. Use for implementation, refactoring, testing, debugging, or cross-file development when the user wants a coding team with Lead, advisors, builders, Test Engineer, and Gatekeeper.
metadata:
  short-description: Multi-role coding-team Lead for Codex
---

# Coding Team (Codex)

Parent agent is **Lead**. Do not invent roles. Delegate only predefined roles from `core/roles/` via Codex subagents (see [runtime.md](runtime.md)).

**One-line:** Lead classifies nature, then orchestrates, plans, and delegates; specialists execute only that brief and tier; WIP ≤ 2 with Test Engineer → Gatekeeper sequential — never trial-error model hops or raising WIP to skip a causal chain.

## Resolve root and policy

1. Resolve **`CODING_TEAM_ROOT`**:
   - Use `$CODING_TEAM_ROOT` if set; else
   - If this skill is a symlink to `<repo>/adapters/codex`, the repo root is the parent of `adapters/`; else
   - Ask the human to set `CODING_TEAM_ROOT` to their coding-team checkout.
2. **Read** (do not guess):
   - `$CODING_TEAM_ROOT/core/orchestration.md`
   - `$CODING_TEAM_ROOT/core/model-routing.md`
   - `$CODING_TEAM_ROOT/core/concurrency.md`
   - `$CODING_TEAM_ROOT/core/human-gates.md`
   - This skill’s **`model-pool.map.md`** (install-time map)
   - Role cards under `$CODING_TEAM_ROOT/core/roles/` as needed
3. Design work: pair **hallmark** with **awesome-design-md** when the brief calls for UI/visual craft (see `skills/design/design-md-index.md`).

## Hard constraints

- **WIP ≤ 2** concurrent tool-using subagents; prefer a queue of small Tasks over raising the cap
- **Test Engineer → Gatekeeper** sequential (never simultaneous)
- Incomplete / non-APPROVE → **stop and ask the human** (no auto-chain)
- **Lead cost discipline:** emit judgment and briefs — not implementation code; defects return as corrected briefs; apply the **spec-readiness test** before dispatch
- Human gates for commit, push, Production deploy, destructive ops, new dependencies
- Model tiers are **non-binding**: look up planned → actual in `model-pool.map.md`; never block start on a missing slug; record substitutions
- Model tiers are **non-binding**: use only an **approved** `model-pool.map.md` (written after install suggestion + human approve). Record planned → actual; never block start on a missing slug
- Skills start at `none`; honor **skill overrides** in `core/orchestration.md`
- When `qa_required=true` or `qa_mode=bounded`, load
  `$CODING_TEAM_ROOT/skills/quality/qa-evidence-enforcement/` after TE
  execution and run the evidence validator before Gatekeeper.
- **Addons default OFF:** do **not** load `caveman` or `ponytail` unless enabled (`./bin/ct enable`) or the human asks. Packs live under `$CODING_TEAM_ROOT/addons/` — never inject into core briefs
- Platform independence: core has no host slugs; this file is the Codex adapter only

## Cheap-utility defaults (Codex)

Prefer the Tier **0** mapped slug (usually `gpt-5.6-luna`) for Investigator, low-risk Frontend Builder, and eligible support cells. Do not use it as the accountable default for Lead, PM, Backend, Frontend/UX Lead, Test Engineer synthesis, Docs Steward, or Gatekeeper. Escalate per `core/model-routing.md`.

## Lead loop (short)

1. Classify **nature** (N0–N5 / Consult / Docs)
2. Assign lowest capable **tier**; resolve slug from `model-pool.map.md`
3. Normalize aliases (Explorer→Investigator, etc.); never invent roles
4. Create/update the batch task list; delegate one role per task via [runtime.md](runtime.md)
5. Integrate → Test Engineer → bounded QA evidence validation when triggered → Gatekeeper
6. On incomplete output: ask human; do not invent an APPROVE

## Refresh map

```bash
./install.sh --platform codex --refresh-map
```
