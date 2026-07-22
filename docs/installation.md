# Installation

One command after clone:

```bash
git clone https://github.com/ericlam2k/coding-team.git
cd coding-team
./bin/ct init
```

| Command | What it does |
|---|---|
| `./bin/ct init` | Install coding-team for Codex + write model-pool map |
| `./bin/ct init --full` | Same + enable caveman & ponytail |
| `./bin/ct status` | Show skill links and addon ON/OFF |
| `./bin/ct refresh` | Refresh model-pool map only |
| `./bin/ct enable caveman,ponytail` | Turn addons on |
| `./bin/ct disable caveman` | Turn an addon off |
| `./bin/ct project /path/to/app` | Append AGENTS.md pointer |

`./install.sh` still exists for advanced flags; normal use is **`./bin/ct`**.

## Prerequisites

- Git
- Python 3.9+ (model-pool scripts)
- OpenAI Codex with local `~/.codex`

## Activate in Codex

```text
Load the coding-team skill. You are Lead Orchestrator.
Read core/orchestration.md, core/model-routing.md, core/human-gates.md, and the installed model-pool.map.md.
Classify my request with nature N0–N5, assign a tier, map the slug, then propose a Sprint → Batch → Task plan before any edits.
WIP ≤ 2. TE → Gatekeeper sequential. Incomplete or non-APPROVE → stop and ask me.
```

## Verify

```bash
./bin/ct status
```

## Optional addons

Default **OFF**. See [addons.md](addons.md).

```bash
./bin/ct init --full
# or later:
./bin/ct enable caveman,ponytail
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| Skill points at old folder | Re-run `./bin/ct init` **from the clone you want** (rewrites symlink) |
| `models_cache.json` missing | Open Codex once, then `./bin/ct refresh` |
| Addon not loading | `./bin/ct enable <name>` then `./bin/ct status` |
