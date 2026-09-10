# Host-neutral platform plan (branch implementation)

Status: QUEUED for `main` (recorded 2026-08-18). Planning only; each step keeps
the evidence + human gates below. No commit/push/merge is admitted by this doc.

## Operating model

- `main` = stable integration target = the Codex runtime checkout. Never edited
  directly for adapter changes.
- Every platform adapter (codex, cursor, cline, opencode) is implemented on its
  own branch: `adapter/<platform>-<slug>` (e.g., `adapter/opencode-wysy-lab`).
- A branch merges to `main` only after: diff review + hermetic evidence bundle +
  Gatekeeper + explicit human approval. No auto-merge; no silent main overwrite.

## Host-neutral rule (all platforms)

- Any change to `core/` or shared surfaces must stay host-neutral: no host
  slugs, host commands, or host-runtime references in core policy, roles,
  templates, or contracts.
- Host-specific code lives only under `adapters/<host>/`.
- Codex-bound runtime (watchdog, checkpoint, flow) rolls host-neutral one feature
  per release in order `watchdog -> checkpoint -> flow`: a host-neutral capability
  interface in `core/`, the Codex implementation adapter-local, parity/smoke
  evidence, CI + Code Reviewer + TE + Gatekeeper, one release each.

## Per-platform model map

- Model pools are host-specific and approved per platform:
  `./bin/ct map propose/approve --platform <platform>`.
- OpenCode: the user approves the opencode map from OpenCode (pending). Until
  approved, tiers are explicitly non-binding.

## OpenCode trial (first branch implementation)

- Branch: `adapter/opencode-wysy-lab`. Lab-first, no public release.
- Plan: SA host-neutral boundary contract -> bootstrap -> smoke probe -> Code
  Reviewer -> TE (`validate-qa-evidence.rb`) -> Gatekeeper -> human approval.
- Acceptance: zero `core/` diff; hermetic receipts at a recorded SHA; no push/
  merge to `main`; model-pool approved or non-binding; confined to the branch.

## Sequencing

- P0: OpenCode trial (this lab branch).
- P1: cursor / cline branch implementations (adapters already exist).
- P2: `core/` prose cleanup + `watchdog -> checkpoint -> flow` migration (one
  release each), after the SA boundary contract is frozen.
