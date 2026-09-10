# OpenCode runtime binding

| Intent | OpenCode action |
|---|---|
| Lead | Root OpenCode session (primary agent) |
| Delegate | Role-card brief as an OpenCode sub-agent/task per `core/roles/` |
| Model | Look up approved `adapters/opencode/model-pool.map.md` (non-binding) |
| Rules load | OpenCode reads `AGENTS.md` from the working directory; `SKILL.md` follows the cline/cursor adapter pattern |
| Concurrency | ≤ 2 tool-using agents; Code Reviewer → QA route → GK under `core/qa-operating-model.md` |
| Permissions | `allow` / `ask` / `deny` in `opencode.json`; no unsandboxed writes |
| Progress / stop | Valid completed handoff or `REVISE` → named in-scope Task; `BLOCK`/invalid output → ask human |

Canonical `code-reviewer` is an independent, read-only, non-final subagent.
Never invent role IDs. Normalize only documented aliases per
`core/orchestration.md`; unknown roles or verdicts fail closed at this adapter
boundary.

## Verification boundary

This table is a binding proposal, not runtime evidence. OpenCode skill load,
delegation, and permission behavior must be proven by an isolated smoke probe
before run receipts count as evidence (see trial scope).
