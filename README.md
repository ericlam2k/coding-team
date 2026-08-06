# WYSY + coding-team

**WYSY = What You See, You Ship.**

Vibe-code, but don't build blind.

WYSY is the visible AI coding control layer for repo-based delivery. Describe a
change in plain English, see the plan and file scope, confirm it, then review
model routing, cost, Test Engineer evidence, and the Gatekeeper decision.

The underlying `coding-team` framework remains platform-independent and keeps
its Sprint → Batch → Task workflow, role cards, WIP ≤ 2, human gates, and
Test Engineer → Gatekeeper sequence. Plain Mode hides backend taxonomy;
Expert Mode exposes it for technical operators.

Current WYSY scaffolding records runs, cost, evidence, and Project Graph facts.
The Codex adapter also has a session/context policy-manifest cache and local
telemetry receipt ([policy-cache](core/policy-cache.md)); it does not claim a
host token meter or provider KV-cache savings. It does not claim a hosted
dashboard, full GraphRAG indexing, or implemented Cursor/Cline runtimes.

---

**Platform-independent multi-agent coding team** — Sprint → Batch → Task, role cards, human gates, abstract model tiers. Adapters for Codex, Cursor, and Cline.

[Installation](docs/installation.md) · [Definitions](docs/definitions.md) · [Workflow](docs/workflow.md) · [Learning, experiments, and distillation](core/learning-and-distillation.md) · [Roles](docs/roles.md) · [Skills](docs/skills.md) · [Addons](docs/addons.md) · [Model pool](docs/model-pool-mapping.md) · [Adapters](docs/adapters.md)

---

## v2 notes

- **Platform independent:** `core/` has no host model slugs. Codex / Cursor / Cline are adapters only.
- **Installation:** `scripts/install-coding-team.sh` exposes Hybrid/Full as the
  host scope choice. Both profiles are map-free; Full uses `bin/ct init --full`
  only to enable supported addons and remains mutually exclusive with Hybrid.

## Quick start

```bash
git clone https://github.com/ericlam2k/coding-team.git
cd coding-team
./scripts/install-coding-team.sh --profile hybrid --platform codex
```

Hybrid links only the platform adapter and conditional QA skill. It does not
refresh model maps or enable addons. To opt into the full framework:

```bash
./scripts/install-coding-team.sh --profile full --platform codex
```

```bash
./scripts/install-coding-team.sh --profile hybrid --platform cursor
./scripts/install-coding-team.sh --profile full --platform codex
./scripts/install-coding-team.sh --check --profile hybrid --platform codex
./bin/ct status
```

Profiles are toggled by rerunning the installer. The marker at
`$CODEX_HOME/coding-team.profile` records the active profile; switching back to
Hybrid removes only addon links owned by this checkout. `bin/ct init` remains
available for adapter setup, while `bin/ct map propose|approve|decline` are the
explicit model-map actions.

## What this is

| Layer | What it does |
|---|---|
| **Core** | Host-agnostic policy: roles, gates, WIP ≤ 2, nature → tier |
| **Skills** | Bundled engineering / quality / process / design packs |
| **Adapters** | Codex, Cursor, Cline runtime binding |
| **Addons** | PM Lean + Agentic Worker — default OFF, toggleable |

## How routing works

1. Lead classifies **nature** (N0–N5 / Consult / Docs).
2. Nature selects an abstract **tier**.
3. Lead uses the **approved** `model-pool.map.md` slug for that tier.
4. Missing slug → next best; record `planned → actual` (never block start).

One-liner: **Premium decide. Eco build. Cheap search/docs. Human gate for irreversible risk.**

## Domain Expert (`[Domain]-Advisor`)

No fixed Talent-Career role. When specialty judgment is needed, Lead **asks for the domain**, then maps:

| Display | Instance ID |
|---|---|
| Talent-Advisor | `talent-advisor` |
| Strategic-Advisor | `strategic-advisor` |
| Security-Advisor | `security-advisor` |
| … | `{domain}-advisor` |

Template: `core/roles/domain-advisor.md` · Rules: `core/domain-advisors.md` · Roles doc: [docs/roles.md](docs/roles.md).

## License

MIT for framework files. Third-party notices: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
