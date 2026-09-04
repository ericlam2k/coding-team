# Dispatch message guard

## Current status

The Customer-0 token-count message guard is `DISPOSED` from the active CLI. A
matched provider run produced identical token use because the local
integration did not modify the provider request. No authoritative automatic
runtime seam was available.

The optional [`prepare-dispatch.py`](../adapters/codex/scripts/prepare-dispatch.py)
formatter remains available. It converts a role (or native agent type) and
plaintext message into the three-field host payload. It is not a gate,
admission check, provider token counter, or execution receipt.

The historical Customer-0 command now fails closed with
`TOKEN-TOOLS-DISPOSED`:

```text
python3 scripts/customer0-token-tools.py invoke guard -- <explicit argv>
```

Historical source, contracts, and evidence remain available. No automatic
token savings, cache reuse, model routing, retry, policy promotion, or release
is claimed. AST remains disabled with `AST-MEMORY-UNSUPPORTED`.
