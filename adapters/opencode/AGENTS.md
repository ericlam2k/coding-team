# OpenCode Adapter for coding-team

This adapter enables OpenCode to use the coding-team orchestration skill
(lab-first trial; no public release).

## Setup

1. Set `CODING_TEAM_ROOT` to the absolute path of this coding-team checkout.
   Example: export CODING_TEAM_ROOT=/Users/quanglam/Documents/Wysy/coding-team

2. Open OpenCode in this checkout. These rules plus `$CODING_TEAM_ROOT/core/`
   govern role invocation, task dispatch, and evidence collection.

3. Optional install: `./bin/ct init --platform opencode`
   Model map: `./bin/ct map propose/approve --platform opencode`

## Usage

- Follow `core/orchestration.md`, role cards under `core/roles/`, and the
  approved `adapters/opencode/model-pool.map.md` when present.
- Shared operating rules: WIP ≤ 2, disjoint writes, Code Reviewer → QA route →
  Gatekeeper under `core/qa-operating-model.md`, and a human
  decision before irreversible actions.
- Evidence: record actual model IDs, exit state, artifacts, and the commit SHA
  for every run; receipts must pass `scripts/validate-qa-evidence.rb` before
  Gatekeeper review.

## Trial Scope (lab)

This adapter is a private lab trial on `adapter/opencode-wysy-lab`. It has no public release.

In scope:
- Reuse `core/` (roles, workflow, templates, model routing) read-only via `CODING_TEAM_ROOT`.
- Hermetic OpenCode run receipts at a recorded SHA as adapter evidence.
- Own OpenCode `model-pool.map.md` once approved.

Out of scope:
- `core/` changes; Codex/WYSY runtime scripts (watchdog, checkpoint, flow); Codex model-pool slugs.
- Push to `origin`, merge to `main`, or any public sync without a separate human approval.
- Third-party skill bundles or redistribution.

Stop rule: any `core/` modification, origin push, or non-hermetic receipt → stop and return to Lead/human.

## Host-neutral rule

Any change to `core/` or shared surfaces must stay host-neutral: no host slugs,
host commands, or host-runtime references in core policy, roles, templates, or
contracts. Host-specific code belongs only under `adapters/<host>/`.

Codex-bound runtime features already developed (watchdog, checkpoint, flow) are
scheduled for rolling host-neutral updates on the product roadmap; do not port
them into `core/` in host-specific form.

## framework-reload

A minimal, host-neutral OpenCode plugin that keeps the WYSY/coding-team
framework available to a session **after OpenCode performs native compaction**.

- **What it does:** hooks `experimental.session.compacting` (fired by OpenCode
  during native compaction, carrying `sessionID`) to remember the session, then
  on the first LLM request after compaction (`experimental.chat.system.transform`
  hook) appends a short *pointer-only* directive to `output.system[0]` (string
  concatenation). The directive references `core/README.md` and the policy files
  — it does **not** embed policy text. `session.compacted` also fires (later,
  after the summary is written); it is consumed but deduped so it cannot cause a
  second injection.
- **Host-neutral & portable:** lives under `adapters/opencode/framework-reload`
  only; registered in `.opencode/opencode.json` via a **repo-relative** path
  (`../adapters/opencode/framework-reload/index.js`), so it works on any
  machine without editing. It touches no host slugs, commands, or runtime
  references in `core/`.
- **Pointer-only / side-effect-free by default:** it mutates only the in-memory
  system prompt and uses the host logger (`ctx.log`); it does **not** emit a chat
  message and does **not** mutate `output.context`. It writes **no files** unless
  `FRAMEWORK_RELOAD_DEBUG=1` is set, in which case it appends a diagnostic host
  log at `~/.config/opencode/framework-reload-plugin.log`. The pending session
  set is bounded (FIFO eviction at 64) and cleared unconditionally on match.
- **Proven activation:** `adapters/opencode/framework-reload/test-activation.mjs`
  simulates the OpenCode hook lifecycle (compacting → transform) and asserts
  exactly-once injection, no double-injection from the late `session.compacted`,
  and re-anchor on genuine re-compaction — run it with `node` to verify without a
  full OpenCode restart. (One live `/compact` observation also confirmed firing.)
- **`core/` must stay untouched:** this plugin references `core/` files by path
  only; never modify `core/` to satisfy it.
