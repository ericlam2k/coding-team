# Incremental Release Plan — coding-team (public)

Status: QUEUED for next release (recorded 2026-08-16). Planning only. No
commit, push, tag, or GitHub Release is admitted by this document; each step
keeps the evidence and human gates below.

## Evidence pinned 2026-08-16

- Live public repo: `ericlam2k/coding-team`, main = `2062cb9`.
- MIT `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `THIRD_PARTY_NOTICES.md` present.
- Addons on main: `pm-lean` only (Caveman/Ponytail removed).
- No WYSY, Customer 0, Agentic Worker, or MoE markers on public main.
- GitHub Releases API returns `[]` — nothing published; `v2.0.0`/`v2.1.0` are bare tags.
- Install contract: adapter + `qa-evidence-enforcement` only; `skills/` (452 files)
  resolves via `CODING_TEAM_ROOT`; role skill load is trigger-based, default `none`,
  so roles operate without a bundle.

## Validated public/commercial matrix

| # | Feature | Classification | Basis |
|---|---|---|---|
| 1 | Role cards + Sprint→Batch→Task workflow | PUBLIC | VERIFIED on main |
| 2 | Skills packs (design/engineering/process/quality) | PUBLIC (in-tree) | VERIFIED; document load contract |
| 3 | Adapters codex/cursor/cline | PUBLIC | VERIFIED |
| 4 | Installer + CLI (install.sh, bin/ct) | PUBLIC | VERIFIED |
| 5 | QA normal/risky + validator | PUBLIC | VERIFIED |
| 6 | Human gates | PUBLIC | VERIFIED |
| 7 | Docs + examples | PUBLIC | VERIFIED |
| 8 | Addons (pm-lean) | PUBLIC opt-in | VERIFIED |
| 9 | Model-pool mapping (read/gated-write) | PUBLIC optional | VERIFIED |
| 10 | Token-optimization tool manifests | PRIVATE | releases/inventory local only |
| 11 | Agentic Worker addon | PRIVATE | absent from public main |
| 12 | WYSY product, strategy, Customer 0 | PRIVATE | separate repo |
| 13 | Marketing/positioning | DEFERRED | human-deferred |
| 14 | Commercial tiers (Pro/Team/Enterprise) | ADVISORY ONLY | never shipped |
| 15 | GitHub Releases with assets | UNAVAILABLE | gap to close |
| 16 | Community v1 free scope | ADVISORY | matches current tree |

## Objective

Keep the public repo alive with a rolling cadence: small validated increments
merged to `main` continuously; tagged GitHub Releases at lower frequency; skill
packs shipped one category per release — not one pack.

## Cadence

- Increments (weekly–biweekly): one to three small merged changes — docs fix,
  one skill pack, installer tweak, example. Each PR: CI lint + skill-structure
  validation → Code Reviewer → Test Engineer evidence → Gatekeeper
  (sequential; release impact requires TE).
- Tagged releases (monthly, ~4–6 increments): `patch` = docs/fixes;
  `minor` = new skill pack or feature; `major` = workflow/policy contract break.
  Each tag publishes a GitHub Release: notes, per-pack asset, CHANGELOG excerpt,
  install quickstart.
- Event-based alternative (weigh with Advisor): tag when N increments
  accumulate, not by calendar, to avoid empty releases.

## Skill-pack sequencing (one pack per release)

1. R1 — `process`: context-engineering, pm-execution, docs-seeker.
2. R2 — `quality` core: debugging, code-review, web-testing
   (`qa-evidence-enforcement` stays in the install contract).
3. R3 — `engineering`: backend-development, frontend-development, databases,
   devops, web-frameworks, react-next-performance, ui-styling,
   system-architecture.
4. R4 — `design`: design-router, anti-ui-slop, hallmark, awesome-design-md, frontend-design, aesthetic,
   ui-ux-pro-max, artifact-theme.
- Quality-first alternative (R2 before R1) stays open: QA/evidence is the
  differentiator and attaches to the already-public QA contract.

Each pack: TE validation on a clean checkout via `CODING_TEAM_ROOT` (skill
loads, SKILL.md valid), skill-metadata validation, Gatekeeper review, human
tag approval.

## Host-neutral roadmap (rolling)

- Any merged change to `core/` or shared surfaces must be host-neutral: no host
  slugs, host commands, or host-runtime references in core policy, roles,
  templates, or contracts; host-specific code lives only under `adapters/<host>/`.
- Codex-bound runtime features (watchdog, checkpoint, flow, codex model-pool
  slugs) are scheduled as rolling host-neutral increments — one feature per
  release, each with CI + TE evidence + Gatekeeper — not one bulk port.
- Host-neutrality is a release blocker for `core/` changes; adapter-only
  changes stay inside `adapters/<host>/`.

## Keep-alive mechanics

- CI: extend `.github/workflows/lint.yml` with skill-structure checks using
  `scripts/validate-skill-metadata.rb` (SKILL.md present, frontmatter valid,
  referenced paths resolve).
- Release manifest: replicate the `releases/inventory/*.json` pattern per
  release — version, packs, asset hashes — public-safe subset only.
- Docs hygiene: replace "bundled" over-claims with "in-tree; loaded via
  `CODING_TEAM_ROOT`"; CHANGELOG entry per release; "what shipped / what's
  next" note per tag.
- Community loop: skill-request issue template, `CONTRIBUTING.md` skill-pack
  checklist, visible public backlog.
- Automation: a draft-only script builds per-pack assets and drafts release
  notes; a human publishes. No automatic tag or release.

## Gates

- Per increment: PR → CI → Code Reviewer → targeted TE when triggered → Gatekeeper → merge to `main`.
- Per release: accumulated increments + deterministic evidence → Code Reviewer
  → fresh TE evidence on the tagged tree → Gatekeeper → explicit human approval
  → tag + GitHub Release.
- Public/private boundary scan (allowlist + marker grep) before every tag.

## Validation status (2026-08-16)

- Product Manager: `VALIDATE_FIRST`; row 10 corrected to PRIVATE; verified
  LICENSE/CONTRIBUTING present; sequencing/cadence `REASONED_NOT_TESTED`.

## Distribution mechanism (Advisor recommendation)

- **DO** extend `install.sh`/`bin/ct` with per-pack category flags
  (`--with-process`, `--with-quality`, ...) that symlink the category into the
  host skill dir — extends the proven adapter pattern; reversible; testable.
- **DO NOT** start with GitHub Release zip assets (manual friction) or keep
  `CODING_TEAM_ROOT`-only (all-or-nothing defeats incremental adoption).
- Cheapest first increment: `--with-process` + CI skill-structure validation,
  then draft-release automation; release manifest deferred until >=2 packs.
- Next owners before any installer change: System Architect validates skill
  dependency/load order; Test Engineer designs the skill-load integration test.

## Validation status (2026-08-16, updated)

- Product Manager: `VALIDATE_FIRST`; row 10 corrected to PRIVATE; sequencing/
  cadence `REASONED_NOT_TESTED`. Two PM evidence claims corrected by Lead:
  MIT LICENSE and CONTRIBUTING.md ARE on public main (verified 2062cb9).
- Contradictor: completed via codex exec, model `Zenmux DS V4P` (cpa-gui;
  planned deepseek-v4-pro-0813; host receipt tokens 29,372) — `proceed-if-addressed`
  (VERIFIED): no leakage in core/docs/scripts/skills/addons/examples; in-tree
  packs must not be documented as bundled/installed; sequencing/cadence
  `REASONED_NOT_TESTED`; failure modes: bundle over-claim, stale pack drift,
  unbounded release automation, missing TE->Gatekeeper gates. Next owner: System
  Architect (freeze pack dependency/load contract).
- Advisor: `VALIDATE_FIRST`; recommends Option B install flags; first pack
  `process`; defer manifest until >=2 packs. Next: SA + TE.
- Lead synthesis: matrix CONFIRMED with row 10 PRIVATE; primary gap is
  unpublished releases (`[]`), not missing skills; skills are in-tree PUBLIC.
