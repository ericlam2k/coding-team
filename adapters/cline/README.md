# Cline adapter (v2)

Install:

```bash
./bin/ct init --platform cline
```

Installation links the adapter only. An optional local model map is shown with
`./bin/ct map propose --platform cline` and written only with the explicit
`./bin/ct map approve --platform cline` command.

Set `CODING_TEAM_ROOT` to this checkout and load `adapters/cline/SKILL.md` (or the `.cline-install/coding-team` symlink created by init).

See [runtime.md](runtime.md) and [docs/adapters.md](../../docs/adapters.md).
