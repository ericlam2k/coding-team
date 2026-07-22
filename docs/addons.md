# Addons (caveman & ponytail)

Standalone skill packs. **Default OFF.** Not injected into coding-team core, roles, or Lead policy.

| Addon | Purpose | Enable |
|---|---|---|
| **caveman** | Full compressed-communication skillset (caveman, commit, review, compress, stats, help, cavecrew) | `./install.sh --platform codex --global --enable caveman` |
| **ponytail** | Full lazy-senior skillset (ladder, bugfix, shortcuts, challenge, check) | `./install.sh --platform codex --global --enable ponytail` |

Both:

```bash
./install.sh --platform codex --global --enable caveman,ponytail
```

Disable:

```bash
./install.sh --platform codex --global --disable caveman
./install.sh --platform codex --global --disable ponytail
```

State: [`addons/toggles.json`](../addons/toggles.json). Details: [`addons/README.md`](../addons/README.md).

## Rules

1. Core never requires these addons.
2. Do not paste addon bodies into every Task brief.
3. Caveman = mouth small (tokens). Ponytail = hands efficient (diff). Safe together.
4. Human gates still apply (commit/push/Production).
