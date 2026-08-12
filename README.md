# coding-team

**A reviewable delivery loop for vibecoders.** Turn a plain-English coding goal into a small, inspectable path from Sprint → Batch → Task—then keep a human in control of what ships.

coding-team is a platform-independent framework for organizing AI-assisted repository work. It gives an agent team a shared shape: named roles, bounded work in progress, explicit acceptance, and evidence before the final review.

[Install](docs/installation.md) · [See the workflow](docs/workflow.md) · [Meet the roles](docs/roles.md) · [Try the marketing pack](docs/marketing/README.md) · [Definitions](docs/definitions.md) · [Skills](docs/skills.md) · [Addons](docs/addons.md) · [Model pool](docs/model-pool-mapping.md) · [Adapters](docs/adapters.md)

## Why it exists

Vibecoding is excellent at getting from idea to motion. The hard part is knowing what the agent is doing, when the work is small enough to review, and whether “done” has evidence behind it.

coding-team makes those decisions visible:

- **Sprint → Batch → Task** keeps a big goal small enough to steer.
- **Role cards** make ownership and boundaries explicit.
- **WIP ≤ 2** limits concurrent tool-using work.
- **Human gates** protect irreversible actions.
- **Test Engineer → Gatekeeper** puts independent evidence before final acceptance.

The result is not “more autonomous.” It is a clearer path to a change you can inspect, test, and consciously accept.

## Choose how the framework speaks

Prefer an everyday explanation, or skip metaphors and go straight to the
technical terms. The [communication guide](docs/communication-style.md) gives
the copy-paste mode choices, and the [validation example](docs/examples/validation-scenario.md)
shows that both modes preserve the same constraints and evidence.

## A first bounded task

```text
Goal: add one small feature
Boundary: touch only the named files
Proof: run the focused check and report changed paths
Stop: pause for review before commit or release
```

Install the adapter for your host, start with one bounded task, and adapt the framework to your project. The core stays host-neutral; Codex, Cursor, and Cline bindings live under `adapters/`.

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
