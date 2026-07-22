# Third-party notices

This repository vendors third-party skills and reference libraries. Framework files authored for coding-team are MIT (see [LICENSE](LICENSE)). Bundled components keep their upstream licenses.

---

## Caveman (Julius Brussee)

- Path: `addons/caveman/`
- License: MIT — see `addons/caveman/LICENSE`
- Copyright: Copyright (c) 2026 Julius Brussee
- Note: **Standalone addon, default OFF.** Not part of coding-team core. Enable with `./install.sh --enable caveman`.

## Ponytail (coding-team)

- Path: `addons/ponytail/`
- License: MIT (same as this repository’s [LICENSE](LICENSE))
- Note: **Standalone addon, default OFF.** Enable with `./install.sh --enable ponytail`.

---

## awesome-design-md (VoltAgent)

- Path: `skills/design/awesome-design-md/`
- License: MIT — see `skills/design/awesome-design-md/LICENSE`
- Copyright: Copyright (c) 2026 VoltAgent

---

## Hallmark

- Path: `skills/design/hallmark/`
- Upstream note: skill text references “Powered by Together AI.”
- **No LICENSE file was present upstream at vendor time.**
- Status: vendored for convenience with attribution. **Confirm redistribution rights before public/commercial redistribution of this subtree.** Fallback: replace with a git submodule pointing at upstream.

---

## Skills adapted from common agent-skill collections

Paths under `skills/engineering/`, `skills/quality/`, `skills/process/`, and parts of `skills/design/` (`frontend-design`, `aesthetic`, `ui-ux-pro-max`, etc.) are adapted from widely circulated agent skill packs. Where an upstream `LICENSE` or notice existed alongside a skill, it was retained in that skill’s directory. If a skill subdirectory lacks an explicit license file, treat it as third-party content requiring the same pre-publish review as Hallmark.

---

Do not remove this file when publishing. When adding a new vendored skill, append a section with path, copyright, and license.
