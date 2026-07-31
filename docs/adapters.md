# Adapters (platform-independent core)

Core policy under `core/` has **no host model slugs**. Adapters bind runtime only.

| Adapter | Status | Install |
|---|---|---|
| [Codex](../adapters/codex/) | **v2 supported** | `./bin/ct init --platform codex` |
| [Cursor](../adapters/cursor/) | **v2 supported** | `./bin/ct init --platform cursor` |
| [Cline](../adapters/cline/) | **v2 supported** | `./bin/ct init --platform cline` |

Auto-detect: `./bin/ct init` (prefers Codex if `~/.codex` exists).

## Shared install behavior (v2)

1. Link/copy the platform adapter skill.
2. **Detect** host model pool (or known defaults).
3. **Show a suggested** tier → slug map.
4. **Ask for approval** (`Y/n`) before writing `model-pool.map.md`.
5. Pass `--yes` only for CI / non-interactive approve.

```bash
./bin/ct init                 # interactive approve
./bin/ct init --yes           # auto-approve suggestion
./bin/ct refresh              # re-propose map + approve again
```

## Binding summary

Same Lead / WIP ≤ 2 / TE→GK / human-gates semantics on every platform; only spawn/resume mechanics differ (see each adapter’s `runtime.md`).
