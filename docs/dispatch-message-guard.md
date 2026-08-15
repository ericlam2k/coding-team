# Dispatch message guard

Status: candidate, not released. Proposed feature version: `1.0.0`.

## Purpose and boundary

`dispatch-message-guard` is a dependency-free Codex adapter boundary that
builds the dispatch message array and applies a caller-supplied token ceiling.
It does not dispatch, choose a model, estimate tokens from characters,
interpret cache state, or provide telemetry authority. Public-core and
commercial/WYSY imports and data remain outside this feature.

Public API:

```python
from adapters.codex.message_guard import build_guarded_messages

result = build_guarded_messages(
    static_system_prompt,
    codebase_structure,
    chat_history,
    active_request,
    token_counter,
    max_tokens=90_000,  # optional lower ceiling; derived default is 260000
)
```

The injected `token_counter` is authoritative for this transaction and is
called exactly once with the completed array. A caller may lower the ceiling,
but may not raise the universal window of `272000` or its derived default ceiling
of `260000`. Dispatch is allowed only
when `token_count < max_tokens`; equality and every higher value reject before
dispatch. Missing, failing, mutating, boolean, negative, or otherwise invalid
counters fail closed.

## Message order and prefix identity

The output order is fixed:

1. the static system prompt;
2. the codebase structure;
3. chat history in its supplied order; and
4. the active request as the absolute final message.

History may contain only `user` and `assistant` entries. A `system` history
entry is rejected. No sorting, merging, trimming, insertion, or role rewriting
is performed.

The first two messages form the static prefix. Its canonical UTF-8 JSON uses
sorted keys, compact separators, `ensure_ascii=false`, and no trailing
newline. The digest is `sha256:<64 lowercase hex>`. Changing the template
version, system prompt, or codebase structure creates a new digest and
invalidates prefix reuse. History and active-request changes do not change the
prefix digest.

## Cache and template observations

The local policy-manifest cache state (`HIT`, `MISS`, or other state) and a
provider prompt-cache receipt are independent observations. Neither proves the
other, proves prefix reuse, proves provider cache use or freshness, grants
authority, changes message ordering, changes the counter result, or demonstrates
token/cost savings. A missing provider receipt is `UNAVAILABLE`. This feature
therefore makes no cache-hit, performance, or cost-saving claim.

Changing `prefix_template_version` is an intentional invalidation event. The
version and resulting prefix digest are returned with an allowed result so a
consumer can correlate a template revision with its evidence; cache behavior
still requires a separate provider receipt.

## Errors and evidence

Rejected results expose no message array. `DispatchGuardError` exposes only a
stable code, optional token count/ceiling, optional prefix digest, and
`decision="REJECT"`; error text does not include message content, private
identifiers, or counter internals. Rejection must result in zero downstream
dispatch/model-selection calls.

The implementation and focused tests are linked rather than reproduced here:

- [frozen contract](../../implementation/architecture-contracts/sprint-2-dispatch-message-guard-v1.md)
- [public implementation](../adapters/codex/message_guard.py)
- [Terra test evidence](../../.coding-team/evidence/s2-dispatch-message-guard-TE_EVIDENCE.md)
- [Gatekeeper decision](../../.coding-team/evidence/s2-dispatch-message-guard-GK_DECISION.md)

Current evidence is 12 focused tests passing, an owned compile pass, and a
scoped nested diff check. Terra and Gatekeeper both identify the same residual:
the injected counter has not been shown to match provider/runtime accounting.

## Activation, release, and rollback

The guard is not wired into runtime dispatch. Counter/runtime parity is
unverified and blocks activation. There is no unguarded fallback. This is a
candidate only; it is not released and its inventory/manifest presence does
not perform a release.

Activation requires fresh parity evidence, the existing human adapter-
activation gate, and the required feature/version evidence. Release selection
must separately use the one-feature rolling-release inventory and human gate;
this document does not authorize either action.

If activation is approved and later rolled back, restore the prior approved
adapter pin and disable dispatch unless that pin supplies an approved guard.
Retain the feature version, prefix digest, and rollback reason in the evidence
record. Git, release, and publication actions remain separately human-gated.
