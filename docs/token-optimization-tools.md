# Token optimisation tools

This page records the verified local tools. They are explicit commands. They do
not select a provider or dispatch a task.

## Commands

Run from `coding-team`:

```sh
./bin/ct tools terminal --timeout-s 2 -- python3 -c 'print("synthetic")'
./bin/ct tools quantize --request-file ./synthetic-request.json
./bin/ct tools guard --request-file ./synthetic-guard.json \
  --authoritative-token-count 259999
```

`terminal` forwards an argument array and returns the exit code and last 20
lines. It fails closed when the POSIX process-group capability is unavailable.
`quantize` deterministically classifies a task. It does not choose a vendor or
start a model. `guard` keeps the static prefix first, history in order, and the
active request last. The caller supplies the authoritative count exactly once.

The universal guard window is `272000` tokens with a `12000` reserve. The derived
exclusive ceiling is `260000`; `259999` is allowed and `260000` is rejected.
Configured limits may be lower, never higher. Invalid limits and a missing,
invalid, or repeated count fail closed.

## AST status

The AST core callable exists and its tests remain available. The `ct tools
skeleton` command is disabled on every platform and returns
`AST-MEMORY-UNSUPPORTED` before it parses arguments, reads a path, or calls the
core. External isolation and a strict cap are deferred. Revisit only after a
representative measured experiment shows at least 20% net end-to-end token
savings and zero containment escapes. Smaller, unavailable, or offset savings
mean `NO_IMPLEMENT`.

## Evidence and limits

The local closeout has 80 passing tests (47 adapter, 16 AST core, 17
quantizer). Provider parity, cache hits, savings, token counts, and currency
are `UNAVAILABLE`; no automatic dispatch is implied. Examples above use
synthetic input and are not performance claims.

Rollback is simple: stop calling these explicit routes and use the existing
workflow. Do not treat the disabled AST route as a fallback implementation.

This page does not grant commit, push, release, or Production approval. A
release candidate also needs the separate inventory and validation gates.
