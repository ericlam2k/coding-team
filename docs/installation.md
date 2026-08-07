# Installation (v2)

## Clone and activate

```bash
git clone https://github.com/ericlam2k/coding-team.git
cd coding-team
./scripts/install-coding-team.sh --profile hybrid --platform codex
```

The default **Hybrid** profile is the low-cost, platform-independent activation:

- links only the selected platform adapter and the conditional QA evidence
  skill;
- keeps the active hybrid QA policy, WIP ≤2, disjoint writes, and TE →
  Gatekeeper sequencing;
- does not refresh a model map or enable optional addons.

The optional **Full** profile is a separate install mode:

```bash
./scripts/install-coding-team.sh --profile full --platform codex
```

Full delegates to `bin/ct init --full`, including model-map approval. Optional
addons remain explicit-only. Switch back explicitly:

```bash
./scripts/install-coding-team.sh --profile hybrid --platform codex
./scripts/install-coding-team.sh --check --profile hybrid --platform codex
./bin/ct status
```

Profiles are mutually exclusive at activation time. The installer records the
active value in `$CODEX_HOME/coding-team.profile` and Hybrid removes only
addon symlinks that point into this checkout; it never deletes unrelated user
files. Use a project-local `CODEX_HOME` when the host sandbox cannot read the
global Codex home.

Both profiles load the same core task-size policy: split work expected to
exceed 120 seconds or cross the width limits, checkpoint at 180 seconds, and
hard-stop at 240 seconds with one bounded handoff. Full mode does not bypass
WIP ≤2, disjoint writes, or TE → Gatekeeper sequencing.

For direct interactive model-map management without profile switching, the
advanced commands remain available:

```bash
./bin/ct init
./bin/ct init --yes              # skip prompt (CI)
./bin/ct init --platform cursor
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

For Risky QA batches, installation also exposes the conditional
`qa-evidence-enforcement` skill and the
`scripts/validate-qa-evidence.rb` promotion validator. It is activated only
when the batch declares `qa_required=true` or `qa_mode=bounded`. The bounded
pass is timeboxed at 120 seconds target / 240 seconds hard stop; timeout is a
blocked evidence result, not an automatic retry.

For a no-dependency activation of only the adapter, core policy, and QA skill,
use the generic installer (the old Codex name remains a compatibility wrapper):

```text
Set CODING_TEAM_ROOT to this clone and load the coding-team skill for your
platform. The installer links the adapter and conditional QA skill.
```

```bash
./scripts/install-coding-team.sh --profile hybrid --platform codex
```

This does not refresh model maps or enable addons. Use `--check` to verify an
existing activation without changing links. `scripts/activate-codex-team.sh`
continues to invoke the same Hybrid Codex path for existing automation.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Map not written | Hybrid does not write maps; choose `--profile full` or run `./bin/ct refresh` |
| Wrong platform symlink | Rerun `./scripts/install-coding-team.sh --profile <profile> --platform <name>` |
| Non-interactive refused | Add `--yes` to the advanced `bin/ct` command |
