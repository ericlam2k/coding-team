# Cursor adapter (v2)

Install:

```bash
./bin/ct init --platform cursor
```

Installation links the adapter only. An optional local model map is shown with
`./bin/ct map propose --platform cursor` and written only with the explicit
`./bin/ct map approve --platform cursor` command.

Link into a project:

```bash
mkdir -p /path/to/project/.cursor/skills
ln -s "$(pwd)/adapters/cursor" /path/to/project/.cursor/skills/coding-team
export CODING_TEAM_ROOT="$(pwd)"
```

See [runtime.md](runtime.md) and [docs/adapters.md](../../docs/adapters.md).
