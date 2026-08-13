# Model-pool mapping

The core framework routes work to abstract capability tiers. A host may map
those tiers to concrete model slugs, but that mapping is local configuration,
not public platform policy.

## Abstract tiers

| Tier | Intent |
| --- | --- |
| 0 | Cheap utility for lookup or lightweight docs |
| 1 build | Everyday implementation |
| 1 validate | Careful validation |
| 2 | Premium planning, debate, or Gatekeeper judgment |
| 3 | Max-risk judgment |

The Lead records `planned → actual` when the runtime supplies a usable
identity. A missing slug or unavailable receipt does not become a fabricated
claim.

## Explicit map flow

Canonical installation does not create a map. When you need one, separate
inspection from approval:

```bash
# Read-only suggestion. No file is written.
./bin/ct map propose --platform codex

# Human-gated write to the local host map.
./bin/ct map approve --platform codex
```

Use `--yes` only when the surrounding automation is itself the explicit
approval gate:

```bash
./bin/ct map approve --platform codex --yes
```

## Portability rule

`core/model-routing.md` stays free of host slugs. Codex, Cursor, and Cline may
expose different pools, names, effort controls, and receipts. Therefore:

- do not copy a concrete map from one host to another;
- do not treat an example map as an availability guarantee; and
- keep `UNAVAILABLE` when the host provides no trustworthy receipt.
