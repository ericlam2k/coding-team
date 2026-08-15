# Model pool mapping (v2)

## Abstract tiers (core — no host slugs)

| Tier | Intent |
|---|---|
| 0 | Cheap utility |
| 1 build | Eco implement |
| 1 validate | Careful validate |
| 2 | Premium plan / debate / Gatekeeper |
| 3 | Max-risk judgment |

## Explicit map flow

```text
setup (no map) → explicit proposal → explicit human approval → write declared map outputs
```

```bash
./bin/ct init                 # adapter/QA setup only; no map write
./bin/ct map propose          # proposal only; no write
./bin/ct map approve          # prompt for explicit approval
./bin/ct map approve --yes    # explicit non-interactive approval
./bin/ct map decline          # no write
./bin/ct refresh --yes        # explicit approval alias
```

Proposal script: [`scripts/propose-model-map.py`](../scripts/propose-model-map.py).

## Codex preference hints (not core policy)

| Tier | Typical suggestion |
|---|---|
| 0 | `gpt-5.6-luna` |
| 1 build / validate | `gpt-5.6-luna` at `max` |
| 2 / 3 | `gpt-5.6-sol` (+ effort) |

Cursor/Cline detectors use that platform’s known pool labels; you can reject and re-run after editing prefs in the script if needed.

## Rules

- Never bake host slugs into `core/model-routing.md`
- Never block task start on a missing slug — record `planned → actual`
- Unapproved proposals must not be treated as live map
- Setup and profile installation leave `model_map_status: NOT_STARTED`.
- Map approval changes only model metadata; it never starts PM, architecture,
  a role, a model, a retry, or a gate.
