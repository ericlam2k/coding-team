# Model pool mapping

Core policy never hardcodes vendor slugs. Install detects the **host model pool** and writes `model-pool.map.md`.

## Abstract → intent

| Tier | Intent |
|---|---|
| 0 | Cheap utility |
| 1 build | Eco implement |
| 1 validate | Careful validate |
| 2 | Premium plan / debate / Gatekeeper |
| 3 | Max-risk judgment |

## Codex v1 preferences (GPT-family)

When the Codex pool is available, the mapper prefers:

| Tier | Preferred slug | Effort hint |
|---|---|---|
| 0 | `gpt-5.6-luna` (alt `gpt-5.4-mini`) | low |
| 1 build | `gpt-5.6-terra` | medium |
| 1 validate | `gpt-5.6-terra` | high |
| 2 | `gpt-5.6-sol` | high |
| 3 | `gpt-5.6-sol` | xhigh / max |

If a preferred slug is missing, pick the closest remaining model by role in the pool (fast → 0, everyday → 1 build, deeper → 1 validate, frontier → 2/3). **Fail loud:** write `planned → actual | not available` in the map and in task handoffs.

## Commands

```bash
./install.sh --platform codex --global --refresh-map
# or
python3 adapters/codex/scripts/detect-model-pool.py
python3 adapters/codex/scripts/apply-pool-map.py --out adapters/codex/model-pool.map.md
```

Example: [`examples/model-pool.map.codex.example.md`](../examples/model-pool.map.codex.example.md).

## Rules

- Never block task start on a missing slug.
- Prefer different family for Contradictor vs Advisor when the pool has multiple families; on GPT-only, use effort + independent subagent and record it.
- Do not edit `core/model-routing.md` to bake in host slugs.
