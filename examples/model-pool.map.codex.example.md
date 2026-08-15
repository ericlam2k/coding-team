# model-pool.map.md (Codex) — example

Generated: `2026-07-21T00:00:00Z` (example only — run `./install.sh --platform codex --refresh-map` for a live map)

Abstract tiers from `core/model-routing.md` → closest available GPT slug.
Tiers are non-binding; record planned → actual in briefs. Never block start on missing identity.

## Available pool

- `gpt-5.6-sol`
- `openai/gpt-5.6-luna-pro`
- `gpt-5.6-luna`
- `gpt-5.5`
- `gpt-5.4`
- `gpt-5.4-mini`

## Map

| Tier | Planned | Actual slug | Effort | Notes |
|---|---|---|---|---|
| **0** | gpt-5.6-luna (or gpt-5.4-mini) | `gpt-5.6-luna` | `medium` | — |
| **1 build** | openai/gpt-5.6-luna-pro | `openai/gpt-5.6-luna-pro` | `max` | — |
| **1 validate** | gpt-5.6-terra + effort high | `gpt-5.6-terra` | `high` | Luna Pro Max fallback |
| **2** | gpt-5.6-sol + effort high | `gpt-5.6-sol` | `high` | — |
| **3** | gpt-5.6-sol + effort xhigh/max | `gpt-5.6-sol` | `xhigh` | — |

## Usage

Lead assigns a tier, then uses **Actual slug** + **Effort** when spawning Codex subagents.
Refresh: `./install.sh --platform codex --refresh-map`
