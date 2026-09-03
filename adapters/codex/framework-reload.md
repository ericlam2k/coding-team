# Codex framework continuity

This is the global Codex adapter rule for session continuity. It is always
loaded with the Coding Team skill through the global skill symlink.

## Lifecycle

1. Before compaction, preserve a bounded handoff containing the objective,
   Sprint/Batch/Task identity, owned paths, acceptance, verified facts,
   evidence references, unknowns, last decision, residual limits, and one next
   action. Never store raw prompts, transcripts, secrets, or private paths.
2. After compaction or a new session, reload the project `AGENTS.md`, this
   adapter skill, current Coding Team policy, the active role card, and the
   handoff before using tools or dispatching a role.
3. Treat the handoff as continuity context only. It does not prove
   implementation, validation, approval, or release.
4. If an official Codex hook supplies `SessionStart` with `source=compact`, the
   global Codex hook may provide the bounded re-anchor as additional context.
   `PreCompact` and
   `PostCompact` receipts correlate the lifecycle; `PostCompact` is not
   restoration proof.
5. If hook delivery or restoration is unavailable or unverified, stop safely
   and perform the reload manually. Do not continue on an assumed “always on”
   state.

## Boundary

This document is host-neutral guidance for the Codex adapter. It does not
install or mutate project/global hook configuration, copy WYSY-private state,
or claim runtime activation. Per-project hook installation remains a separate
human-gated operation with fresh Test Engineer and Gatekeeper evidence.

## STUCK boundary

Framework reload continuity and execution supervision are separate controls.
When Codex has no verified host deadline, admitted commands must use
`scripts/stuck-watchdog.py`; otherwise a raw host call may continue until the
provider or host stops it. The watchdog emits one checkpoint, cancels at the
configured hard stop, and records one `BLOCKED` `STUCK_REPORT` with no retry.
