# Adapters

| Adapter | Status | Binding |
|---|---|---|
| [Codex](../adapters/codex/) | **v1 implemented** | Parent Lead + subagents; skill under `~/.codex/skills/coding-team` |
| [Cursor](../adapters/cursor/) | Stub | Future: Task + agent cards; same abstract tiers |
| [Cline](../adapters/cline/) | Stub | Future: `team_*` tools; same abstract tiers |

Install with an unimplemented platform exits non-zero:

```bash
./install.sh --platform cursor  # not implemented in v1
```

## Codex binding (summary)

| Intent | Action |
|---|---|
| Lead | Parent Codex session |
| Delegate | Subagent + role path + ≤250-word run prompt + path ranges |
| Model | Look up `model-pool.map.md` for the assigned tier |
| Resume | One immediate follow-up; else fresh + persisted brief |
| Concurrency | ≤2 tool-using subagents; TE → GK sequential |
| Stop | Incomplete / non-APPROVE → ask human |

Details: [`adapters/codex/runtime.md`](../adapters/codex/runtime.md).
