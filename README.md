# coding-team

**Vibe-code, but don't build blind.** Turn a plain-English idea into one small,
reviewable change with a clear scope, useful proof, and your decision at the
end.

`coding-team` is a standalone public, lite framework. It provides role cards,
bounded work, evidence rules, and human gates that can be used by a project
without access to a private product or hosted service.

[Install](docs/installation.md) · [Project scope](docs/project-scope.md) · [See the workflow](docs/workflow.md) · [Meet the roles](docs/roles.md) · [Try the example](docs/examples/validation-scenario.md) · [Definitions](docs/definitions.md) · [Skills](docs/skills.md) · [Addons](docs/addons.md) · [Model pool](docs/model-pool-mapping.md) · [Adapters](docs/adapters.md)

## Why it helps

AI coding is fast. The hard part is knowing what the agent is changing, when
the work is small enough to review, what was actually tested, and whether it
is ready to ship.

coding-team makes those decisions visible:

- **Sprint → Batch → Task** keeps a big goal small enough to steer.
- **Role cards** make ownership and boundaries explicit.
- **WIP ≤ 2** limits concurrent tool-using work.
- **Human gates** protect irreversible actions.
- **Test Engineer → Gatekeeper** puts independent evidence before final acceptance.

The result is a visible path from request to reviewed change—not a promise of
more autonomy. You keep the final decision.

## See it in one minute

Start with one request. Make its boundary visible, run the focused check, and
pause for your decision when the evidence is ready or incomplete.

![Illustrative diagram: a plain-English goal moves through scoped work, evidence, and a human ship decision.](docs/examples/assets/coding-team-lite-loop.svg)

This illustrative visual shows the public loop: request → bounded work →
evidence → your decision. The [communication guide](docs/communication-style.md)
keeps the language clear without changing the underlying constraints or
evidence.

## A first bounded task

```text
Goal: add one small feature
Boundary: touch only the named files
Proof: run the focused check and report changed paths
Stop: pause for review before commit or release
```

Install the adapter for your host, start with one bounded task, and adapt the
framework to your project. The core stays host-neutral; Codex, Cursor, and
Cline bindings live under `adapters/`. See [Project scope](docs/project-scope.md)
for the public release boundary.

---

## Install in one command

For most people, the friendly entrypoint detects the available host and can
optionally prepare a first project. Press Enter to skip the project prompt:

```bash
./install.sh
```

It can optionally add a pointer to your first project:

```bash
./install.sh --project /path/to/your/project
```

If the folder is missing or cannot be updated, installation still completes
and the command explains how to prepare it later.

For CI, scripts, or a fully explicit setup, skip all prompts:

```bash
./install.sh --platform codex --no-questionnaire
```

## Advanced install and explicit extensions

The canonical installer links the selected adapter and conditional QA support:

```bash
./scripts/install-coding-team.sh --platform codex
```

There is one public installation path. Model maps and addons are explicit
extensions; see [Installation](docs/installation.md).

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
3. Lead uses a host-local approved `model-pool.map.md` slug when one exists.
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
