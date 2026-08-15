# Session policy cache and Lead telemetry

**Status:** active framework guidance; local-only; no host billing claim

## Why this exists

The Codex host may inject the adapter skill on every turn. A repository cannot
disable that host behavior or guarantee a provider-side KV-cache hit. It can,
however, stop the Lead from repeatedly reopening unchanged repository policy
files and can make the result observable.

The cache covers stable policy text only. It is a reuse/invalidation manifest,
not a second policy source, permission layer, router, or memory runtime.

## Session protocol

At the first Lead turn in a session, load the stable policy bundle and run:

```bash
python3 coding-team/scripts/policy-cache.py init \
  --session-id "${WYSY_POLICY_SESSION_ID:-}" \
  --context-fingerprint "${WYSY_POLICY_CONTEXT_FINGERPRINT:-}"
```

On later Lead turns, check the manifest:

```bash
python3 coding-team/scripts/policy-cache.py check \
  --session-id "${WYSY_POLICY_SESSION_ID:-}" \
  --context-fingerprint "${WYSY_POLICY_CONTEXT_FINGERPRINT:-}"
```

`HIT` (the helper's compatibility label is `CACHE_HIT`) means unchanged policy
text may be reused without reloading it into the Lead/model context. The helper
still reads each local file to recompute its SHA-256 drift check; that local
I/O is reported as `policy_files_hashed`, not model-token consumption. `MISS`
is a fresh policy read;
`INVALIDATED` means refresh before making a policy-sensitive decision;
`BYPASSED` means no trustworthy active-context identity was supplied. A
`BYPASSED` or `UNAVAILABLE` result fails closed and cannot authorize a
policy-sensitive delegation. `refresh` is an explicit alias for `init` and is
required after a policy edit, install/refresh, checkout/pull, or a human
request.

The session ID and opaque active-context fingerprint are host-provided when
possible. If either is absent, the helper records `BYPASSED`; it does not
pretend that a local file manifest detects context compaction. A new Codex
conversation, context compaction that removes the policy from active context,
or uncertainty about the active session/context requires a fresh load with a
new identity even when an old manifest exists.

### Internal fallback when the host supplies no IDs

The current Codex adapter does not expose these two identities automatically.
For a bounded local session, set them manually once and rotate the context
value after compaction or starting a new conversation:

```bash
export WYSY_POLICY_SESSION_ID=wysy-local-session-01
export WYSY_POLICY_CONTEXT_FINGERPRINT=wysy-local-context-01
```

Then run `init` once and `check` on later policy-dependent turns. Do not reuse
the values across unrelated conversations, and do not claim provider token or
KV-cache savings from this local fallback. A missing/uncertain identity must
remain `BYPASSED`.

## Stable policy bundle

The helper fingerprints these files by default:

- `AGENTS.md`
- `adapters/codex/SKILL.md`
- `adapters/codex/runtime.md`
- `adapters/codex/model-pool.map.md`
- `core/orchestration.md`
- `core/model-routing.md`
- `core/concurrency.md`
- `core/human-gates.md`
- `core/policy-cache.md`

Use `--include-learning` when the task includes learning, experiments,
performance evidence, fallback correction, or distillation; this adds
`core/learning-and-distillation.md` to the bundle.

The manifest stores only an opaque manifest identity, adapter/policy scope,
session/context key, opaque policy-root scope, relative paths, size/mtime, and
SHA-256 digests at
`.coding-team/cache/policy-manifest.json`. It does not store prompts, role-card
contents, secrets, provider data, or a replacement copy of policy.

## What is not cached

- **Role cards:** Lead still reads and hashes the complete selected canonical
  card before delegation and honors `role-card.check`, stale detection, and
  `CONSUMED=UNVERIFIED` boundaries. A cached policy hit never authorizes a
  role or proves runtime consumption.
- **Dynamic task facts:** request, scope, files, model choice, evidence, and
  human decisions are loaded just in time from the current brief/run.
- **System instructions and host tools:** the repository cannot cache or
  override them.

## Telemetry and monitoring receipt

Every cache command appends one local event to:

```text
.coding-team/runs/policy-cache-events.jsonl
```

The event is a `POLICY_MANIFEST_CACHE` Monitor observation. It records the
canonical cache state (`MISS`, `HIT`, `INVALIDATED`, `BYPASSED`, or
`UNAVAILABLE`), context status, manifest provenance, files read/reused,
invalidation reasons, and named local-helper timing. Token and currency fields
are always explicit: they are numeric only when a host/runtime receipt supplies
a named source and units; otherwise they remain `null` with status
`UNAVAILABLE`. The helper cannot measure model input/output tokens.

Lead handoffs and performance entries must show these fields rather than omit
them:

```yaml
policy_cache: MISS | HIT | INVALIDATED | BYPASSED | UNAVAILABLE
policy_files_read: <integer or unavailable>
policy_files_hashed: <integer or unavailable>
elapsed_seconds: <measured local/helper value or unavailable>
input_tokens: <number or null>
output_tokens: <number or null>
total_tokens: <number or null>
telemetry_source: host_runtime | local_helper | unavailable
persisted_event: <repo-relative path or NOT_PERSISTED>
```

`elapsed_seconds` is not human time-to-ship and is not provider cost. Missing
host telemetry must be shown as `unavailable`, never inferred from elapsed
time, model tier, or response length.

## Invalidation and safety

Refresh when the manifest is missing/invalid, the session, policy root, or
source revision changes, a file set or digest changes, the active context was
compacted, a high-risk or learning trigger requires the full bundle, or the
user asks for refresh. A failed check or a missing context fingerprint stops
policy-sensitive delegation until refresh with a valid identity.

This cache does not relax WIP ≤2, sequential TE → Gatekeeper, human gates,
model-map approval, FIO boundaries, or learning-promotion rules.
