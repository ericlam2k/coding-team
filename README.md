# coding-team

**Platform-independent multi-agent coding team** — Sprint → Batch → Task, role cards, human gates, abstract model tiers. Adapters for Codex, Cursor, and Cline.

[Installation](docs/installation.md) · [Definitions](docs/definitions.md) · [Workflow](docs/workflow.md) · [Roles](docs/roles.md) · [Skills](docs/skills.md) · [Addons](docs/addons.md) · [Model pool](docs/model-pool-mapping.md) · [Adapters](docs/adapters.md)

---

## v2 notes

- **Platform independent:** `core/` has no host model slugs. Codex / Cursor / Cline are adapters only.
- **Installation:** `./bin/ct init` **suggests** a model map and **shows it for your approval** before writing. Use `--yes` only when you intentionally skip the prompt.

## Quick start

```bash
git clone https://github.com/ericlam2k/coding-team.git
cd coding-team
./bin/ct init
```

You will see a suggested tier → slug table, then:

```text
Approve and write this model map? [Y/n]:
```

```bash
./bin/ct init --yes              # auto-approve (CI)
./bin/ct init --platform cursor
./bin/ct init --full             # + caveman/ponytail (Codex)
./bin/ct status
```

## What this is

| Layer | What it does |
|---|---|
| **Core** | Host-agnostic policy: roles, gates, WIP ≤ 2, nature → tier |
| **Skills** | Bundled engineering / quality / process / design packs |
| **Adapters** | Codex, Cursor, Cline runtime binding |
| **Addons** | Caveman + Ponytail — default OFF, toggleable |

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
