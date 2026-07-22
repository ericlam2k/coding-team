# Installation

This guide is for **humans** installing coding-team into Codex (v1). Cursor and Cline are not implemented yet.

## Prerequisites

- Git
- Python 3.9+ (for model-pool scripts)
- OpenAI Codex / ChatGPT Codex desktop or CLI with a local `~/.codex` home
- Network not required for install after clone (pool detection reads local Codex cache)

## 1. Clone

```bash
git clone https://github.com/ericlam2k/coding-team.git
cd coding-team
```

Or as a submodule inside an existing project:

```bash
cd /path/to/your-app
git submodule add https://github.com/ericlam2k/coding-team.git vendor/coding-team
cd vendor/coding-team
```

## 2. Install (Codex)

### Global (recommended for personal use)

```bash
./install.sh --platform codex --global
```

What this does:

1. Resolves `CODEX_HOME` (default `~/.codex`)
2. Symlinks `adapters/codex` → `$CODEX_HOME/skills/coding-team`
3. Detects available models from `~/.codex/models_cache.json` (+ config default)
4. Writes `model-pool.map.md` next to the Codex skill (and refreshes the example under `examples/`)
5. Prints an activation prompt

### Project-scoped

```bash
./install.sh --platform codex --project /path/to/your-app
```

Links the skill for that project workflow and can append a short pointer into the project’s `AGENTS.md` (see installer output).

### Refresh map only

After Codex adds/removes models:

```bash
./install.sh --platform codex --global --refresh-map
```

## 3. Activate in Codex

In a new Codex chat on your project:

```text
Load the coding-team skill. You are Lead Orchestrator.
Read core/orchestration.md, core/model-routing.md, core/human-gates.md, and the installed model-pool.map.md.
Classify my request with nature N0–N5, assign a tier, map the slug, then propose a Sprint → Batch → Task plan before any edits.
Lead cost discipline: briefs and routing only — no implementation code from Lead.
Prefer Tier 0 (often Luna) for Investigator / low-risk UI; escalate per model-routing.
WIP ≤ 2. TE → Gatekeeper sequential. Incomplete or non-APPROVE → stop and ask me.
```

Optional: copy [AGENTS.md](../AGENTS.md) into your consumer repo root (or merge the snippet) so every session picks up the pointer.

## 4. Verify

```bash
ls -la ~/.codex/skills/coding-team
# should point at .../coding-team/adapters/codex

cat ~/.codex/skills/coding-team/model-pool.map.md
# should list tiers 0 / 1-build / 1-validate / 2 / 3 with real slugs
```

## Environment variables

| Variable | Meaning |
|---|---|
| `CODEX_HOME` | Codex home (default `~/.codex`) |
| `CODING_TEAM_ROOT` | Absolute path to this repo checkout (adapters resolve core/skills relative to it) |

If you move the clone, re-run `./install.sh` so the symlink stays valid.

## Uninstall

```bash
rm -f ~/.codex/skills/coding-team
# remove any AGENTS.md pointer you added manually
```

## Other platforms

```bash
./install.sh --platform cursor   # exits: not implemented in v1
./install.sh --platform cline    # exits: not implemented in v1
```

See [adapters.md](adapters.md).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `models_cache.json` missing | Open Codex once so it refreshes models, then `--refresh-map` |
| Symlink broken after move | Re-run install from the new clone path |
| Wrong models mapped | Edit preferences only via re-detect; do not hardcode slugs into `core/model-routing.md` |
| Skill not visible | Confirm path `~/.codex/skills/coding-team/SKILL.md` exists |
