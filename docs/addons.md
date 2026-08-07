# Addons (PM Lean)

The PM Lean skill pack is standalone, **default OFF**, and never injected into
coding-team core, roles, Lead policy, or approval gates.

| Addon | Purpose | Enable |
|---|---|---|
| **pm-lean** | Explicit-only PM assumption triage and experiment design | `./install.sh --platform codex --global --enable pm-lean` |

Disable:

```bash
./install.sh --platform codex --global --disable pm-lean
```

State: [`addons/toggles.json`](../addons/toggles.json). Details:
[`addons/README.md`](../addons/README.md).

## Rules

1. Core orchestration, roles, and human gates do not depend on PM Lean.
2. Use at most one PM Lean skill inside the existing Product Manager call.
3. It adds no routing, agents, approval authority, or auto-chain.
