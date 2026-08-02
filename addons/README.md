# Standalone addons (toggleable)

These packs live **outside** coding-team core. They are **default OFF** and must not be injected into Lead/role policy unless explicitly enabled.

| Addon | What | License |
|---|---|---|
| [caveman/](caveman/) | Full Caveman skillset (compressed communication, commit/review/compress/stats/help/cavecrew) — upstream Julius Brussee | MIT — see `caveman/LICENSE` |
| [ponytail/](ponytail/) | Full Ponytail skillset (lazy-senior YAGNI ladder, root-cause fixes, `ponytail:` shortcuts) | MIT (coding-team) |
| [pm-lean/](pm-lean/) | Explicit-only PM assumption triage and experiment-design support | MIT — see `pm-lean/LICENSE` |

## Toggle state

See [toggles.json](toggles.json). Defaults:

```json
"caveman": { "enabled": false },
"ponytail": { "enabled": false },
"pm-lean": { "enabled": false }
```

## Enable / disable (Codex)

```bash
./bin/ct enable caveman,ponytail
./bin/ct disable caveman
./bin/ct status
./install.sh --platform codex --global --enable pm-lean
```

(Advanced: `./install.sh --platform codex --global --enable …` still works.)

When enabled, install symlinks the addon into `$CODEX_HOME/skills/<name>` (or the pack’s primary skill path). When disabled, those symlinks are removed. **Core `coding-team` skill stays unchanged.**

## Rules

1. Core orchestration / roles / human gates never require caveman or ponytail.
2. Do not paste addon bodies into `core/` or force them in every Task brief.
3. User (or install toggle) turns them on; user turns them off.
4. Both may be on together: caveman = mouth small; ponytail = hands efficient.
5. PM Lean is explicit-only, stays inside the existing Product Manager call, and adds no routing, agents, approval authority, or auto-chain.
