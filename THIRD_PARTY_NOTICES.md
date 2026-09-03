# Third-party notices

This repository vendors third-party skills and reference libraries. Framework files authored for coding-team are MIT (see [LICENSE](LICENSE)). Bundled components keep their upstream licenses.

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

## anti-ui-slop (UIZZE via GitHub awesome-copilot)

- Path: `skills/design/anti-ui-slop/`
- Upstream repository: https://github.com/github/awesome-copilot
- Upstream path: `skills/anti-ui-slop/`
- Exact upstream commit: `5eaae7e2cde26b5cf86682fb31e758da0288aef7`
- Vendoring: copied unchanged, including upstream `CHECKSUMS.sha256`,
  `LICENSE`, `NOTICE`, `MODIFICATIONS.md`, and packaged-stack manifest
- Included license file: Apache License 2.0 — see
  `skills/design/anti-ui-slop/LICENSE`
- Metadata discrepancy retained: `SKILL.md` declares `license: MIT`, while the
  included license file is Apache-2.0. This notice records the upstream state
  and does not reclassify it.
- Packaged design stack provenance: version `4.1.1`, commit
  `5a149f3fdb1b5793f10567233b1dcab98fc305fd`, license `Apache-2.0`, as recorded
  unchanged in `skills/design/anti-ui-slop/MANIFEST.json`
- Nested notice: `skills/design/anti-ui-slop/NOTICE` attributes the
  `reference/ios.md` material derived from ehmo's MIT-licensed
  `platform-design-skills` work.

---

## Skills adapted from common agent-skill collections

Paths under `skills/engineering/`, `skills/quality/`, `skills/process/`, and parts of `skills/design/` (`frontend-design`, `aesthetic`, `ui-ux-pro-max`, etc.) are adapted from widely circulated agent skill packs. Where an upstream `LICENSE` or notice existed alongside a skill, it was retained in that skill’s directory. If a skill subdirectory lacks an explicit license file, treat it as third-party content requiring the same pre-publish review as Hallmark.

---

Do not remove this file when publishing. When adding a new vendored skill, append a section with path, copyright, and license.
