# Cline runtime binding

| Intent | Cline action |
|---|---|
| Lead | Coordinating teammate |
| Delegate | `team_delegate_task` when exposed; else `team_task` + `team_run_task` |
| Model | Look up approved `model-pool.map.md` (non-binding) |
| Status | `team_status` before run when available |
| Concurrency | ≤2 tool-using teammates; TE → GK sequential |
| Stop | Incomplete / non-APPROVE → ask human |

Never invent role IDs. Normalize aliases per `core/orchestration.md`.
