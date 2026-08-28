# Token optimization tools

## Current status

The Customer-0 overlay is private and local-only. A matched provider trial
showed no change in input or output tokens because the local integration did
not modify the provider request. The quantizer, message guard, and rollback
integration are therefore disposed from the active CLI.

The retained tool is compact terminal. It bounds command output and is invoked
only when the user or caller requests it:

```text
python3 scripts/customer0-token-tools.py status
python3 scripts/customer0-token-tools.py invoke terminal -- <explicit argv>
```

Quantize and guard invocations fail closed with `TOKEN-TOOLS-DISPOSED`.
Historical contracts and evidence remain available. There is no scheduler,
automatic retry, model routing, token-savings claim, or public release.

## Boundaries

- Configuration and observations stay under `.coding-team/customer-0/` with
  `storage_scope=LOCAL_ONLY` and `export_status=NOT_REQUESTED`.
- Historical token claims require authoritative runtime/provider receipts.
  Character counts, output length, elapsed time, and model tier are not token
  receipts.
- Candidate scoring and decay review remain human-review evidence only. They
  cannot mutate policy, routing, release, or activation state.

## AST file skeleton

AST remains disabled with `AST-MEMORY-UNSUPPORTED`. It is not a public or
automatic token tool.

Authoritative implementation/status sources:

- [`scripts/customer0-token-tools.py`](../../scripts/customer0-token-tools.py)
- [`token-optimization Customer-0 contract`](../../implementation/architecture-contracts/sprint-2-token-optimization-customer0-v1.md)
