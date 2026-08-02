# PM Lean addon

Optional, explicit-only Product Manager decision support. It is default OFF and never changes core orchestration, roles, model tiers, WIP, batches, human gates, test evidence, or approval.

## Included skills

| Skill | Use |
|---|---|
| `pm-lean-assumption-triage` | Rank uncertain product assumptions and name the human decision. |
| `pm-lean-experiment-design` | Design the smallest safe test with metric, threshold, and kill criterion. |

Use at most one PM Lean skill per Product Manager task; it counts as that task’s primary skill. Both run in the existing Product Manager call: zero spawned agents, model calls, and tool calls. Existing `skills/process/pm-execution/wwas/` and `outcome-roadmap/` remain the source for those artifacts.

Enable only when needed:

```bash
./install.sh --platform codex --global --enable pm-lean
```

See [UPSTREAM.md](UPSTREAM.md) and [LICENSE](LICENSE).
