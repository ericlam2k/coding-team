# Standalone addons (toggleable)

These packs live **outside** coding-team core. They are **default OFF** and must not be injected into Lead/role policy unless explicitly enabled.

| Addon | What | License |
|---|---|---|
| [pm-lean/](pm-lean/) | Explicit-only PM assumption triage and experiment-design support | MIT — see `pm-lean/LICENSE` |
| [agentic-worker/](agentic-worker/) | Explicit bounded-task implementation and A11 evidence overlay | External supplied pack — see `agentic-worker/SOURCE.md` |

## Toggle state

See [toggles.json](toggles.json). Defaults:

```json
"pm-lean": { "enabled": false },
"agentic-worker": { "enabled": false }
```

## Enable / disable (Codex)

```bash
./bin/ct status
./install.sh --platform codex --global --enable pm-lean
./install.sh --platform codex --global --enable agentic-worker
./install.sh --platform codex --global --disable agentic-worker
```

(Advanced: `./install.sh --platform codex --global --enable …` still works.)

When enabled, install symlinks the addon into `$CODEX_HOME/skills/<name>` (or the pack’s primary skill path). When disabled, those symlinks are removed. **Core `coding-team` skill stays unchanged.**

## Rules

1. Core orchestration / roles / human gates never require an addon.
2. Do not paste addon bodies into `core/` or force them in every Task brief.
3. User (or install toggle) turns them on; user turns them off.
4. PM Lean is explicit-only, stays inside the existing Product Manager call, and adds no routing, agents, approval authority, or auto-chain.
5. Agentic Worker is explicit-only for bounded app-development tasks and adds no routing, agents, approval authority, or auto-chain.
