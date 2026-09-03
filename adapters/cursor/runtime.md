# Cursor runtime binding

| Intent | Cursor action |
|---|---|
| Lead | Parent Agent (never a Lead subagent) |
| Delegate | `Task` with role card path + ≤250-word run prompt + path ranges |
| Model | Look up approved `model-pool.map.md` for assigned tier |
| Resume | One immediate follow-up via `resume`; else fresh Task |
| Concurrency | ≤2 ordinary tool-using Tasks plus at most one optional read-only, non-authoritative supervisor relay (maximum child lanes = 3 only when admitted; never a third ordinary lane); Code Reviewer → conditional Test Engineer → Gatekeeper sequential |
| Stop | Reconcile handle and artifacts; preserve partial work; unchanged route stays blocked |

Canonical role IDs live in `core/roles/`. Prefer `.cursor/agents/<id>.md` in the consumer project when present; otherwise Read the role card from `CODING_TEAM_ROOT`.

A hard stop ends one route, not the authorized objective. Cursor records
`COMPLETE`, `PARTIAL`, or `NO_PROGRESS`, then continues only through a priced,
materially changed smaller route. Human input remains required for scope,
authority, provider, risk, or existing-gate changes.
