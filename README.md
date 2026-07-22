# coding-team

**Platform-independent multi-agent coding team** — Sprint → Batch → Task, role cards, human gates, and abstract model tiers that map to your host’s model pool at install time.

> **v1 priority:** [OpenAI Codex](https://chatgpt.com/codex). Cursor and Cline adapters are stubs.

[Installation](docs/installation.md) · [Definitions](docs/definitions.md) · [Workflow](docs/workflow.md) · [Roles](docs/roles.md) · [Skills](docs/skills.md) · [Model pool](docs/model-pool-mapping.md) · [Adapters](docs/adapters.md)

---

## What this is

A reusable **agent operating system** you clone into (or beside) any project:

| Layer | What it does |
|---|---|
| **Core** | Host-agnostic policy: roles, gates, WIP ≤ 2, nature → tier routing |
| **Skills** | Bundled engineering, quality, process, and design skills (Hallmark + awesome-design-md) |
| **Adapters** | Runtime binding (Codex first) |
| **Install** | Detects the host model pool and writes `model-pool.map.md` |

It is **not** tied to any product codebase. Bring your own stack.

## Quick start (Codex)

```bash
git clone https://github.com/ericlam2k/coding-team.git
cd coding-team
./install.sh --platform codex --global
```

Then in Codex, activate the `coding-team` skill (or paste the activation prompt from [docs/installation.md](docs/installation.md)).

Project install (symlink into a consumer repo):

```bash
./install.sh --platform codex --project /path/to/your-app
```

Refresh the model map after your Codex models change:

```bash
./install.sh --platform codex --global --refresh-map
```

## How routing works

1. Lead classifies work **nature** (N0–N5 / Consult / Docs).
2. Nature selects an abstract **tier** (0 / 1-build / 1-validate / 2 / 3).
3. Install maps tiers → real slugs from **your** model pool (Codex: prefer GPT Luna / Terra / Sol).
4. Missing slug → next best in class; record `planned → actual` (never block start).

**Lead cost discipline:** Lead emits briefs and routing — not implementation code. **Tier 0 / Luna-class** is the default for Investigator and low-risk UI; escalate on conflict or risk.

One-liner: **Premium decide. Eco build. Cheap search/docs. Human gate for irreversible risk.**

## Team roles (canonical IDs)

| ID | Role |
|---|---|
| `lead` | Parent orchestrator (never spawn as a subagent) |
| `product-manager` | Scope / acceptance consult |
| `advisor` | Pre-build technical verdict |
| `contradictor` | Pre-build challenge |
| `investigator` | Read-only repo map |
| `backend-engineer` | Scoped backend writes |
| `frontend-ux-lead` | UX contract / design review |
| `frontend-builder` | Scoped UI writes |
| `test-engineer` | Independent validation |
| `docs-steward` | Durable documentation |
| `gatekeeper` | Post-evidence accept / revise / block |

Details: [docs/roles.md](docs/roles.md) · cards in [`core/roles/`](core/roles/).

## Bundled skills (highlights)

- **Engineering:** backend-development, frontend-development, databases, devops, web-frameworks, ui-styling, react-next-performance
- **Quality:** debugging, code-review, web-testing, sequential-thinking, problem-solving
- **Process:** context-engineering, pm-execution, docs-seeker
- **Design:** **Hallmark** + **awesome-design-md** (paired), plus frontend-design, aesthetic, ui-ux-pro-max

See [docs/skills.md](docs/skills.md) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Repository layout

```text
core/           # platform-agnostic policy, roles, templates
skills/         # bundled skills (engineering / quality / process / design)
adapters/       # codex (v1) · cursor/cline stubs
docs/           # user manual
install.sh      # clone → install → map pool
AGENTS.md       # optional drop-in pointer for consumer projects
```

## License

MIT for framework files we author. Bundled third-party skills keep their own licenses — see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

**Pre-publish note:** Hallmark currently ships without an upstream LICENSE file. Confirm redistribution rights before treating this repo as fully cleared for commercial redistribution of that subtree; fallback is submodule-to-upstream.
