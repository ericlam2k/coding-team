# Installation (v2)

## One command

```bash
git clone https://github.com/ericlam2k/coding-team.git
cd coding-team
./bin/ct init
```

What happens:

1. Auto-detect platform (Codex / Cursor / Cline) or pass `--platform …`
2. Link the adapter skill
3. **Show a suggested model map** (tier → slug)
4. **Ask you to approve** before writing any map file
5. Print next steps

```bash
./bin/ct init --yes              # skip prompt (CI)
./bin/ct init --platform cursor
./bin/ct init --full             # Codex + enable caveman/ponytail after map approve
./bin/ct status
./bin/ct refresh                 # new suggestion + approve again
```

## Why approve the map?

Core is **platform-independent** (abstract tiers only). Host slugs differ (Codex GPT Luna/Terra/Sol vs Cursor pool vs Cline). The installer **suggests** a mapping; you confirm so a bad auto-pick never silently becomes policy.

## Activate

Set `CODING_TEAM_ROOT` to this clone, load the coding-team skill for your platform, then:

```text
You are Lead. Read core/orchestration.md, core/model-routing.md, human-gates.md,
and the approved model-pool.map.md. Classify N0–N5, assign tier, use mapped slug.
WIP ≤ 2. TE → Gatekeeper sequential. Incomplete → ask me.
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| Map not written | You answered `n` — run `./bin/ct refresh` and approve |
| Wrong platform symlink | `./bin/ct init --platform <name>` from this clone |
| Non-interactive refused | Add `--yes` |
