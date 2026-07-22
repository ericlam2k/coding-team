# Standalone addons (toggleable)

These packs live **outside** coding-team core. They are **default OFF** and must not be injected into Lead/role policy unless explicitly enabled.

| Addon | What | License |
|---|---|---|
| [caveman/](caveman/) | Full Caveman skillset (compressed communication, commit/review/compress/stats/help/cavecrew) — upstream Julius Brussee | MIT — see `caveman/LICENSE` |
| [ponytail/](ponytail/) | Full Ponytail skillset (lazy-senior YAGNI ladder, root-cause fixes, `ponytail:` shortcuts) | MIT (coding-team) |

## Toggle state

See [toggles.json](toggles.json). Defaults:

```json
"caveman": { "enabled": false },
"ponytail": { "enabled": false }
```

## Enable / disable (Codex)

```bash
# from coding-team repo root
./install.sh --platform codex --global --enable caveman
./install.sh --platform codex --global --enable ponytail
./install.sh --platform codex --global --enable caveman,ponytail

./install.sh --platform codex --global --disable caveman
./install.sh --platform codex --global --disable ponytail
```

When enabled, install symlinks the addon into `$CODEX_HOME/skills/<name>` (or the pack’s primary skill path). When disabled, those symlinks are removed. **Core `coding-team` skill stays unchanged.**

## Rules

1. Core orchestration / roles / human gates never require caveman or ponytail.
2. Do not paste addon bodies into `core/` or force them in every Task brief.
3. User (or install toggle) turns them on; user turns them off.
4. Both may be on together: caveman = mouth small; ponytail = hands efficient.
