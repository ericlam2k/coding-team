# Cursor adapter (v2)

Install:

```bash
./bin/ct init --platform cursor
```

Shows a suggested model map for approval, then writes `adapters/cursor/model-pool.map.md`.

Link into a project:

```bash
mkdir -p /path/to/project/.cursor/skills
ln -s "$(pwd)/adapters/cursor" /path/to/project/.cursor/skills/coding-team
export CODING_TEAM_ROOT="$(pwd)"
```

See [runtime.md](runtime.md) and [docs/adapters.md](../../docs/adapters.md).
