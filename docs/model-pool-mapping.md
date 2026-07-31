# Model pool mapping (v2)

## Abstract tiers (core — no host slugs)

| Tier | Intent |
|---|---|
| 0 | Cheap utility |
| 1 build | Eco implement |
| 1 validate | Careful validate |
| 2 | Premium plan / debate / Gatekeeper |
| 3 | Max-risk judgment |

## Install flow

```text
detect pool → suggest map → human approve → write model-pool.map.md
```

```bash
./bin/ct init          # shows suggestion, asks [Y/n]
./bin/ct init --yes    # approve without prompt
./bin/ct refresh       # re-run suggestion + approval
```

Proposal script: [`scripts/propose-model-map.py`](../scripts/propose-model-map.py).

## Codex preference hints (not core policy)

| Tier | Typical suggestion |
|---|---|
| 0 | `gpt-5.6-luna` |
| 1 build / validate | `gpt-5.6-terra` |
| 2 / 3 | `gpt-5.6-sol` (+ effort) |

Cursor/Cline detectors use that platform’s known pool labels; you can reject and re-run after editing prefs in the script if needed.

## Rules

- Never bake host slugs into `core/model-routing.md`
- Never block task start on a missing slug — record `planned → actual`
- Unapproved proposals must not be treated as live map
