# Cursor runtime binding

| Intent | Cursor action |
|---|---|
| Lead | Parent Agent (never a Lead subagent) |
| Delegate | `Task` with role card path + ≤250-word run prompt + path ranges |
| Model | Look up approved `model-pool.map.md` for assigned tier |
| Resume | One immediate follow-up via `resume`; else fresh Task |
| Concurrency | ≤2 tool-using Tasks; TE → GK sequential |
| Stop | Incomplete / non-APPROVE → ask human |

Canonical role IDs live in `core/roles/`. Prefer `.cursor/agents/<id>.md` in the consumer project when present; otherwise Read the role card from `CODING_TEAM_ROOT`.
