# coding-team: Public vs Commercial Pack Summary (v2)

Status: QUEUED for next release (recorded 2026-08-16). Planning and positioning
only. No commit, push, tag, release, or paid-product claim is authorized by
this document.

## Executive summary

`coding-team` is a portable, host-neutral operating model for AI coding
agents: roles, bounded Sprint -> Batch -> Task delivery, readiness templates,
evidence review, model-tier routing, and human approval gates.

Today it ships starter adapters for **Codex, Cursor, and Cline**. Pi,
OpenCode, and Claude Code are roadmap targets, not current support.

The core stays public and developer-friendly. Commercial value comes from
adapter maturity, automation, dashboards, policy packs, evidence tooling, and
support -- not from locking the core workflow.

## Classification key

- `PUBLIC`: present on public `main` (`2062cb9`) and safe for public surfaces.
- `ROADMAP`: planned, not implemented, and not presented as shipped.
- `PRIVATE`: WYSY-private; excluded from public surfaces.
- `ADVISORY`: packaging hypothesis only; no shipped or verified claim.

## Product positioning

### Public

`coding-team` is an open, platform-independent multi-agent coding team
framework. It provides role-based orchestration, Sprint -> Batch -> Task
workflow, human gates, model-tier routing, reusable role cards and templates,
and starter adapters for Codex, Cursor, and Cline.

### Commercial

`coding-team Pro` is the governance and evidence layer for teams running
production AI-assisted delivery. It adds production-hardened adapters,
evidence automation, blocker/retry diagnostics, Gatekeeper report
generation, team policy packs, visual dashboards, and commercial support.

## Strategic recommendation

Launch the public version first as a limited developer preview. Do not launch
a paid product until:

- Pi and OpenCode adapters are working and validated;
- the Codex adapter passes a fresh preview validation;
- evidence-bundle workflow is automated;
- blocker/retry policy is implemented and tested;
- third-party skill licensing is audited (not just noticed);
- at least 3 non-Customer-0 baseline demos are published in the public repo.

## Public vs commercial feature table

| Feature area | Public | Commercial | Status |
|---|---|---|---|
| Core framework | Included | Included | `PUBLIC` |
| Sprint -> Batch -> Task workflow | Included | Included with enhanced controls | `PUBLIC` |
| Canonical roles | Included | Included with advanced customization | `PUBLIC` |
| Lead / PM / Advisor / Contradictor / Investigator roles | Included | Included | `PUBLIC` |
| Backend / Frontend / Code Reviewer / Test Engineer roles | Included | Included | `PUBLIC` |
| Gatekeeper role | Basic review decision | Advanced evidence-based review | `PUBLIC` basic |
| Human-gate policy | Basic policy + decision template | Structured decision packages and audit trail | `PUBLIC` basic |
| Task brief template | `task-brief.md` | Enforced readiness validation | `PUBLIC` basic |
| Evidence template | `qa-evidence.json` + `final-report.md` | Auto-generated evidence bundle | `PUBLIC` basic |
| Blocker / retry policy | Basic bounded guidance | Automated trigger and blocker classification | `PUBLIC` basic / `ROADMAP` automation |
| Model-tier routing | Included | Enhanced routing profiles per runtime | `PUBLIC` |
| Codex adapter | Primary supported | Production-grade (validation required) | `PUBLIC` / `ADVISORY` |
| Cursor adapter | Supported | Supported pack | `PUBLIC` |
| Cline adapter | Supported | Supported pack | `PUBLIC` |
| Pi adapter | Not included | Packaged skills, templates, extensions | `ROADMAP` |
| OpenCode adapter | Not included | AGENTS.md, templates, workflows | `ROADMAP` |
| Claude Code adapter | Not included | Adapter pack | `ROADMAP` |
| Install script | Basic `install.sh` | Hardened installer and diagnostics | `PUBLIC` |
| Benchmark scenarios | Public examples | Full benchmark suite and reports | `PUBLIC` examples / `ROADMAP` suite |
| Visual / evidence dashboards | Not included | Included | `ROADMAP` |
| Run history | Manual | Included | `ROADMAP` |
| Policy packs | Basic public policies | QA, security, governance, delivery packs | `PUBLIC` basic / `ADVISORY` |
| Team templates | Basic `core/templates/` | Advanced team and project templates | `PUBLIC` |
| Commercial support | Not included | Included | `ADVISORY` |
| Third-party license handling | MIT + notices present | Audited and maintained | `PUBLIC` / audit required |
| Best use case | Solo devs, early adopters, OSS feedback | Teams, consultants, agencies, AI-native orgs | `ADVISORY` |

## Recommended public launch scope

Include:

- Core role and team operating model;
- Codex-first adapter plus supported Cursor/Cline adapters;
- basic installation guide;
- task-brief, evidence, and review-decision templates;
- basic public policies (human gates, QA operating model, concurrency);
- public examples with clear experimental status.

Exclude:

- paid or enterprise claims;
- full multi-platform compatibility claims;
- unverified third-party skill redistribution;
- autonomous-delivery claims;
- WYSY-private terms such as MoE, Stuck Diagnostic, or Creative Pack.

## Commercial pack scope

Include as roadmap/advisory:

- production-hardened Codex, Pi, OpenCode, and Claude Code adapters;
- Cursor and Cline adapter packs;
- evidence automation and Gatekeeper report generation;
- blocker/retry diagnostics;
- human-gate decision package generator;
- visual run and evidence dashboards;
- QA, security, and delivery governance packs;
- benchmark suite, support, and onboarding.

## Packaging model

Free/public: developers exploring agentic workflows, solo builders, open-source
projects, early adopters. Position as "the open agentic engineering team OS."

Commercial/Pro: AI-native teams, consultants, agencies, startups shipping with
AI coding agents. Position as "the governance and evidence layer for
production AI coding teams." Advisory until the strategic gates pass.

## Suggested roadmap

- v0.1 Public preview baseline: current public tree, pending first tagged
  release.
- v0.2 Policy pack: artifact-readiness, Gatekeeper evidence, human-gate, and
  bounded retry/blocker policies. No MoE or private terms.
- v0.3 Pi adapter: Pi skills, prompt templates, package structure, one demo.
- v0.4 OpenCode adapter: AGENTS.md, workflow templates, one demo.
- v0.5 Benchmark gallery: backend API, dashboard chart, timeout/blocker,
  Gatekeeper evidence, human-gate irreversible-decision scenarios.
- v1.0 Commercial beta: adapter packs, evidence automation, dashboards, policy
  packs, support package.

## Final recommendation

Launch the public limited preview after the first tagged release and boundary
scan; keep the commercial pack advisory until its evidence gates pass.

Proposed tagline: `coding-team: the team operating system for AI coding
agents.`
