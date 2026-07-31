# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] — 2026-07-31

### Notes (release)

- **Platform independence:** Core stays host-agnostic (abstract tiers only). Codex, Cursor, and Cline are first-class adapters — install via `./bin/ct init --platform …` or auto-detect.
- **Installation / model map:** Init **suggests** a tier→slug map, **prints it for human approval**, and writes `model-pool.map.md` only after `Y` (or `--yes` for non-interactive).

### Added

- `scripts/propose-model-map.py` — detect → suggest → approve → write
- Cursor + Cline adapter skills + `runtime.md` (no longer stubs-only)
- `./bin/ct init` interactive approval flow; `--yes`, `--platform`, `--full`

### Changed

- Docs/README rewritten for v2 install UX
- Adapters doc: all three platforms supported under shared approval flow

## [0.3.1] — 2026-07-22

### Added

- Simple CLI: `./bin/ct init` (and `status` / `refresh` / `enable` / `disable` / `project`)
- Docs/README quickstart reduced to one command after clone

## [0.3.0] — 2026-07-22

### Added

- Standalone **addons/** (default OFF): full caveman + ponytail skillsets
- `./install.sh --enable` / `--disable`

## [0.2.0] — 2026-07-22

### Added

- Lead cost discipline, Luna-class Tier 0 defaults, skill overrides, alias normalization

## [0.1.0] — 2026-07-21

### Added

- Initial platform-agnostic core, Codex adapter, bundled skills, GitHub docs
