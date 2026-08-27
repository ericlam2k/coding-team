# Model map

Core uses task tiers, not fixed model names. A model map connects those tiers
to models available on one host.

## Simple rule

**Premium decide. Eco build. Cheap search/docs. Human gate for irreversible
risk.**

| Tier | Use |
| --- | --- |
| 0 | Cheap search/docs |
| 1 build | Eco build |
| 1 validate | Careful validation |
| 2 | Premium decision, debate, or review |
| 3 | Max-risk judgment |

## How the proposal works

The installer:

1. reads the selected host's model list and configuration;
2. lists every valid model ID it finds; and
3. suggests one model for each tier.

GPT names in the example map are references only. The proposer does not require
a gpt-* prefix or a specific provider. Names such as ecobuild and
frontier-think are simple hints, not proof of model quality. The full pool is
shown so you can correct the suggestion.

If a tier hint is missing, the proposer chooses a fallback from the detected
pool and labels it as a heuristic. A missing model or runtime receipt remains
unavailable; it is never invented.

## Commands

Preview the map without writing a file:

```bash
./bin/ct map propose --platform codex
```

Approve and write the local host map:

```bash
./bin/ct map approve --platform codex
```

Use --yes only when the surrounding automation is the explicit approval:

```bash
./bin/ct map approve --platform codex --yes
```

The map is host-specific. Do not copy it between Codex, Cursor, and Cline.
Record planned → actual when the runtime provides the model identity.
