# Standalone addons (toggleable)

These packs live **outside** coding-team core. They are **default OFF** and must not be injected into Lead or role policy unless explicitly enabled.

| Addon | What | License |
|---|---|---|
| [pm-lean/](pm-lean/) | Explicit-only PM assumption triage and experiment-design support | MIT — see `pm-lean/LICENSE` |

## Toggle state

See [toggles.json](toggles.json). The PM Lean addon is disabled by default:

```json
"pm-lean": { "enabled": false }
```

## Enable / disable (Codex)

```bash
./bin/ct enable pm-lean
./bin/ct disable pm-lean
./bin/ct status
./install.sh --platform codex --global --enable pm-lean
```

When enabled, the installer symlinks the addon skills into
`$CODEX_HOME/skills/<name>`. When disabled, those symlinks are removed.
**Core coding-team policy stays unchanged.**

## Rules

1. Core orchestration, roles, human gates, and approval authority never depend on PM Lean.
2. User (or the explicit install toggle) turns it on; the user turns it off.
3. PM Lean stays inside the existing Product Manager call: no routing, spawned agents, approval authority, or auto-chain.
