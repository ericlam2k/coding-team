# Addons

Standalone skill packs. **Default OFF.** Not injected into coding-team core, roles, or Lead policy.

| Addon | Purpose | Enable |
|---|---|---|
| **pm-lean** | Explicit PM assumption triage and experiment design | `./install.sh --platform codex --global --enable pm-lean` |
| **agentic-worker 0.1.0** | Bounded app-development implementation plus A11 evidence | `./install.sh --platform codex --global --enable agentic-worker` |

Disable:

```bash
./install.sh --platform codex --global --disable agentic-worker
```

State: [`addons/toggles.json`](../addons/toggles.json). Details: [`addons/README.md`](../addons/README.md).

## Rules

1. Core never requires these addons.
2. Do not paste addon bodies into every Task brief.
3. Agentic Worker = bounded implementation + evidence.
4. Human gates still apply (commit/push/Production).
5. Agentic Worker can be rolled back independently with `--disable agentic-worker`; core remains installed.
