# OpenCode adapter (v2, lab)

Lab-first OpenCode adapter for coding-team. Private trial on
`adapter/opencode-wysy-lab`; no public release.

## Install

```bash
./bin/ct init --platform opencode
```

Installation links the adapter only. An optional local model map is shown with
`./bin/ct map propose --platform opencode` and written only with the explicit
`./bin/ct map approve --platform opencode` command.

## Use

Set `CODING_TEAM_ROOT` to this checkout, open OpenCode in this repo, and follow
`adapters/opencode/AGENTS.md` (root instruction file) + `adapters/opencode/runtime.md`.
Copy the bootstrap prompt from `adapters/opencode/INIT.md` to start a session.

See [runtime.md](runtime.md), [AGENTS.md](AGENTS.md), [INIT.md](INIT.md) and
[docs/adapters.md](../../docs/adapters.md).
