# Coding Team — AGENTS.md drop-in

Paste this into a consumer project’s `AGENTS.md` (or run `./bin/ct project <path>`).

## Coding Team (Codex)

This project may use the **coding-team** orchestration skill for Sprint → Batch → Task multi-role work.

### Setup

1. Install once (from the coding-team checkout):

   ```bash
   ./scripts/install-coding-team.sh --platform codex
   # optional consumer pointer:
   ./bin/ct project /path/to/this/repo
   ```

2. Set the checkout root (if the skill cannot infer it from the symlink):

   ```bash
   export CODING_TEAM_ROOT=/path/to/coding-team
   ```

3. In Codex, use the **Coding Team** skill (`$coding-team`).

### Lead rules (short)

- Resolve `CODING_TEAM_ROOT` (env, or parent of `adapters/` when the skill is a symlink to `adapters/codex`).
- Read `core/model-routing.md`, concurrency/human-gates when present, role cards under `core/roles/`, and the approved local `model-pool.map.md` only when explicitly configured.
- **WIP ≤ 2 ordinary** concurrent tool-using subagents, plus at most one
  optional read-only, non-authoritative supervisor relay (maximum child lanes
  = 3 only when that relay is admitted; never a third ordinary lane).
- **Code Reviewer → conditional Test Engineer → Gatekeeper**; TE and
  Gatekeeper remain sequential when TE is required.
- Incomplete / non-APPROVE → **ask the human**; do not invent acceptance.
- Design: start at `$CODING_TEAM_ROOT/skills/design/design-router.md`; it
  selects one primary generator and requires rendered inspection before a
  material UI completion claim.

Codex, Cursor, and Cline are host adapters. The core remains host-neutral.

### Host-neutral rule

Any change to `core/` or shared surfaces must remain host-neutral. Host-specific
commands, models, and runtime live only under `adapters/<host>/`. Codex-bound
features (watchdog, checkpoint, flow) are being rolled to host-neutral on the
roadmap.
