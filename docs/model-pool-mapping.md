# Model map

Core uses task tiers, not fixed model names. A model map connects those tiers
to models available on one host.

## Simple rule

**Premium decide. Eco build. Cheap search/docs. Human gate for irreversible
risk.**

| Tier | Use |
| --- | --- |
| 0 | Cheap search/docs |
| 1 build | Eco build |
| 1 validate | Careful validation |
| 2 | Premium decision, debate, or review |
| 3 | Max-risk judgment |

## How the proposal works

Installation and mapping are separate. The user-invoked Codex detector reads
model fields from its cache, structured TOML configuration, `available_models`,
and explicitly referenced model catalogs and agent configs. It preserves exact
slugs and source provenance; it does not read auth files, scan the whole home
directory, probe providers, or infer alias equivalence. Catalog/config presence
is not proof of a callable host route. Missing or malformed inputs are reported.

The proposer lists all detected options. It does not rank names, suffixes,
numeric versions, or provider brands. Without explicit choices it prints
`UNMAPPED`, not an invented capability or cost tier. Public benchmark, effective
cost, and runtime/effort evidence remain `UNVERIFIED`; this version does not
fetch or certify benchmarks. A catalog `free` suffix is not privacy, quota, or
effective-cost evidence.

Supply an explicit selection JSON with `tiers`, optional per-`roles` overrides,
`families`, and optional `notes`. Each route contains `primary`, `fallback`, and
optional `effort`/`fallback_effort`. Choices must be distinct and in the pool.
Every tier and model-assigned role must be complete before approval.

System Architect and backend Gatekeeper are risk-qualified routes. The proposal
must carry separate `standard` and `high` rows: standard selects
`claude-opus-5`, high selects `claude-fable-5-1`, and both declare
`gpt-6-astra` / `high` as an explicit fallback. Fallback metadata never causes
an automatic retry or model switch; use it only in a new authorized dispatch.

PM/SA and Advisor/Contradictor must have disjoint declared family sets, including
fallback choices. Families are explicit metadata, not string-splitting guesses.
This enforces the operator's independence constraint, not independent reasoning
quality. Actual dispatch must recheck the family after any authorized change.

TE has `test-engineer:design` (premium) and `test-engineer:implement` (eco)
choices. When needed, freeze scenarios before implementation, implement the
tests economically, then run deterministic tests with the local test runner;
repeated execution does not need another model. No new role or auto-routing is
created, and role cards are unchanged. Failures return to Lead, not automatic
fallback or retry.

These changes use separation of concerns (identity vs capability vs approval),
explicit configuration instead of string heuristics, and content-bound approval
to prevent approving a different proposal after a pool or selection changes.

## Commands

Preview every option without writing a map:

```bash
./bin/ct map propose --platform codex
```

Preview explicit provisional choices (paths are relative to your current directory):

```bash
./bin/ct map propose --platform codex --selection /path/to/selection.json
```

Add `--json` for machine-readable inventory, choices, problems and digest.
Approval requires complete routes, no discovery warnings, the exact displayed
digest, and explicit acceptance that benchmark/cost/route evidence is missing:

```bash
./bin/ct map approve --platform codex --selection /path/to/selection.json \
  --approve-digest EXACT_DISPLAYED_DIGEST --accept-unverified --yes
```

This command writes only the installed Codex skill's `model-pool.map.md`. It
does not change `config.toml`, the session model, provider settings, or examples.
An existing map is never silently overwritten: preserve it and resolve the
destination explicitly before replacement. A changed pool, selection, notes,
family metadata or warning changes the approval digest. Proposal-only wins over
write flags. Without `--yes`, the command only previews.

The legacy `apply-pool-map.py` supports `--propose-only`; its old direct-write
path is disabled so it cannot bypass selection and digest checks. The host-neutral
proposer does not fabricate Cursor/Cline pools when no live detector is wired.
Do not copy maps between hosts. Record planned and actual identity separately.
