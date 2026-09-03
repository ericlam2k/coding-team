# model-pool.map.md (Codex) — example

Generated: `2026-07-21T00:00:00Z` (example only — run `./bin/ct map propose --platform codex` for a current suggestion)

Abstract tiers from `core/model-routing.md` → closest available host slug.
Selection rule: **Premium decide. Eco build. Cheap search/docs. Human gate for irreversible risk.**
Tiers are non-binding; record planned → actual in briefs. Never block start on missing identity.

## Available pool

- `gpt-5.6-sol`
- `gpt-5.6-terra`
- `gpt-5.6-luna`
- `gpt-5.5`
- `gpt-5.4`
- `gpt-5.4-mini`

## Map

| Tier | Planned | Actual slug | Effort | Notes |
|---|---|---|---|---|
| **0** | cheap search/docs | `gpt-5.6-luna` | `medium` | — |
| **1 build** | eco build | `gpt-5.6-terra` | `medium` | — |
| **1 validate** | careful validation | `gpt-5.6-terra` | `high` | — |
| **2** | premium decide | `gpt-5.6-sol` | `high` | — |
| **3** | max-risk judgment | `gpt-5.6-sol` | `xhigh` | — |

## Usage

Lead assigns a tier, then uses **Actual slug** + **Effort** when spawning Codex subagents.
Inspect: `./bin/ct map propose --platform codex`
Approve/write: `./bin/ct map approve --platform codex`
