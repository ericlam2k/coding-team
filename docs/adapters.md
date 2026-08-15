# Adapters (platform-independent core)

Core policy under `core/` has **no host model slugs**. Adapters bind runtime only.

`--platform` selects the host adapter (Codex/Cursor/Cline). Installation has
one profile-free scope: adapter plus conditional QA support. Legacy
`--profile hybrid|full` flags are deprecated aliases for the same install and
never enable addons or write a model map.

| Adapter | Status | Install |
|---|---|---|
| [Codex](../adapters/codex/) | **v2 supported** | `./bin/ct init --platform codex` |
| [Cursor](../adapters/cursor/) | **v2 supported** | `./bin/ct init --platform cursor` |
| [Cline](../adapters/cline/) | **v2 supported** | `./bin/ct init --platform cline` |

Auto-detect: `./bin/ct init` (prefers Codex if `~/.codex` exists).

## Shared install behavior (v2)

1. Link/copy the platform adapter skill and QA support.
2. Leave `model_map_status: NOT_STARTED`; setup never writes a map.
3. Optionally **show a suggested** tier → slug map with an explicit proposal;
   rerun it after provider, API-proxy, model, or credential changes.
4. Approve only through the separate map action; pass `--yes` only to that
   approval in CI/non-interactive use.

```bash
./bin/ct init                 # adapter/QA setup only; map-free
./bin/ct map propose          # proposal only; no write
./bin/ct map approve          # explicit approval (prompted)
./bin/ct map approve --yes    # explicit non-interactive approval
./bin/ct map decline          # decline without writing
./bin/ct refresh --yes        # explicit approval alias
```

## Binding summary

Same Lead / WIP ≤ 2 / TE→GK / human-gates semantics on every platform; only spawn/resume mechanics differ (see each adapter’s `runtime.md`).
