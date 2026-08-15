# Coding Team — AGENTS.md drop-in

Paste this into a consumer project’s `AGENTS.md` (or run `./install.sh --platform codex --project <path>`).

## Coding Team (Codex)

This project may use the **coding-team** orchestration skill for Sprint → Batch → Task multi-role work.

### Setup

1. Install once (from the coding-team checkout):

   ```bash
   ./install.sh --platform codex --global
   # optional consumer pointer:
   ./install.sh --platform codex --project /path/to/this/repo
   ```

2. Set the checkout root (if the skill cannot infer it from the symlink):

   ```bash
   export CODING_TEAM_ROOT=/path/to/coding-team
   ```

3. In Codex, use the **Coding Team** skill (`$coding-team`).

### Lead rules (short)

- Resolve `CODING_TEAM_ROOT` (env, or parent of `adapters/` when the skill is a symlink to `adapters/codex`).
- Resolve the stable policy bundle once per session/context with
  `coding-team/scripts/policy-cache.py`; reuse only a `HIT` with matching
  opaque session and context identities. Refresh on policy drift, context
  loss/compaction, high-risk/learning work, or a human request. A
  `BYPASSED`/`UNAVAILABLE` result fails closed. If the host exposes no
  identities, use the manual local fallback in `core/policy-cache.md` and
  rotate the context value after compaction. Read the complete selected role
  card separately for every delegation; role cards are never satisfied by the
  policy cache.
- **WIP ≤ 2** concurrent tool-using subagents.
- **Test Engineer → Gatekeeper** sequential only.
- Incomplete / non-APPROVE → **ask the human**; do not invent acceptance.
- At material Batch/Sprint close, record learning disposition; never silently promote a run observation into policy or routing.
- Load `core/learning-and-distillation.md` for learning records, `EXP-*`/PDCA, fallback-mode, performance, or distillation work; experiments remain bounded and human-decided.
- Every handoff/status receipt includes cache state, files read/reused, local
  elapsed time when measured, token status/source, and the local event path;
  missing host/runtime token data remains `unavailable`.
- Design: pair **hallmark** with **awesome-design-md** under `$CODING_TEAM_ROOT/skills/design/`.

Host adapters for Cursor and Cline are **not implemented in v1**.
