# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] — 2026-07-22

### Added

- Standalone **addons/** (default OFF, toggleable — not injected into core):
  - Full **caveman** pack (MIT, Julius Brussee)
  - Full **ponytail** skillset (ladder, bugfix, shortcuts, challenge, check)
- `./install.sh --enable` / `--disable` for caveman and ponytail
- `addons/toggles.json` + [docs/addons.md](docs/addons.md)

## [0.2.0] — 2026-07-22

### Added

- Lead cost discipline (judgment not volume; spec-readiness test)
- Cheap-utility / Luna-class Tier 0 role defaults + escalation rules
- Skill overrides (`context-engineering`, `sequential-thinking`, `problem-solving`)
- Alias normalization table; Lean/Agile vocabulary nest
- Mid-batch incomplete → stop-for-human; Production vs preview gate note
- Role capacity hints on Investigator and Frontend Builder

### Changed

- Codex adapter SKILL and docs (installation, definitions, model-pool mapping) aligned to new policy

## [0.1.0] — 2026-07-21

### Added

- Platform-agnostic core: orchestration, human gates, concurrency, abstract model tiers
- Eleven canonical role cards and brief/handoff templates
- Codex adapter with install script and GPT-family pool mapper
- Bundled engineering, quality, process, and design skills (Hallmark + awesome-design-md)
- User manual under `docs/` (installation, definitions, workflow, roles, skills, adapters, model pool)
- GitHub community files (Contributing, Code of Conduct, issue/PR templates)

### Notes

- Cursor and Cline adapters are stubs in v1
- Hallmark redistribution rights should be re-confirmed before treating the vendored tree as fully cleared
