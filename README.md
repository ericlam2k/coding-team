# coding-team

**Platform-independent multi-agent coding team** — Sprint → Batch → Task, role cards, human gates, abstract model tiers. Adapters for Codex, Cursor, and Cline.

[Installation](docs/installation.md) · [Definitions](docs/definitions.md) · [Workflow](docs/workflow.md) · [Roles](docs/roles.md) · [Skills](docs/skills.md) · [Addons](docs/addons.md) · [Model pool](docs/model-pool-mapping.md) · [Adapters](docs/adapters.md)

---

## v2 notes

- **Platform independent:** `core/` has no host model slugs. Codex / Cursor / Cline are adapters only.
- **Installation:** `scripts/install-coding-team.sh` activates the lightweight Hybrid profile by default. The optional Full profile uses `bin/ct init --full` and is mutually exclusive with Hybrid.

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
available for advanced, interactive model-map setup.

## What this is

| Layer | What it does |
|---|---|
| **Core** | Host-agnostic policy: roles, gates, WIP ≤ 2, nature → tier |
| **Skills** | Bundled engineering / quality / process / design packs |
| **Adapters** | Codex, Cursor, Cline runtime binding |
| **Addons** | PM Lean decision support — default OFF, explicit-only |

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
