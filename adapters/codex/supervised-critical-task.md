# Supervised critical-task runner (Codex adapter)

This private Codex adapter runs one critical Coding Team task in a bounded,
observable process. A critical task is source mutation, Test Engineer evidence,
Gatekeeper work, or contract/policy work where an untracked change or missing
evidence could damage a gate. The runner is evidence tooling, not an approval,
release, or deployment mechanism.

## Guarded launch

Before launch, the caller must provide:

- a clean candidate checkout pinned to `candidate_commit`, with its root digest;
- a fresh `prepare-dispatch.py` result with `status=READY`, the expected
  `dispatch_id`, and a plaintext `spawn` object; encrypted-only briefs and
  `fork_turns=none` are rejected;
- a unique absolute artifact path for this `attempt_id`, a tracked profile and
  its SHA-256 digest, and a new receipt path; and
- one focused validation command plus an adaptive `0 < target < hard_stop`
  timing profile.

The runner binds the attempt with
`task_id + run_id + attempt_id + artifact_path + candidate_commit`. It launches
the approved route as one `codex exec` child and uses the existing
`stuck-watchdog.py` as the only timer and process-group cancellation authority.
The child performs the task and then exactly one focused validation. Broad
regressions are a separate Test Engineer task.

## Invocation

The public command surface is deliberately small:

```sh
python3 adapters/codex/scripts/supervised-critical-task.py \
  run ATTEMPT.json RECEIPT.json
```

`ATTEMPT.json` contains the validated attempt context, READY-dispatch file and
identity, owned paths, profile digest, validation command, and timing values.
For the supervisor's internal second stage, the script accepts:

```sh
python3 adapters/codex/scripts/supervised-critical-task.py \
  internal-worker '{"state_path":"...","command":["..."],"validation_command":["..."]}'
```

Use `--help` for the two subcommands. Inputs are fail-closed and the command
shape is constrained by the script; do not pass an arbitrary task command as a
substitute for a READY dispatch.

## Receipt outcomes

The single terminal receipt classifies the attempt using frozen precedence:
`UNHANDED_MUTATION`, `TRANSPORT_FAILURE`, `TEST_LONG`,
`VALIDATION_FAILURE`, `NO_ARTIFACT`, then `COMPLETED`. It records bounded
identity, commit, artifact, mutation, exit, privacy, and next-action fields.
The watchdog emits one checkpoint, waits for process-group quiescence, and
publishes one receipt. A `BLOCKED` result preserves observed work as
unaccepted evidence. Every outcome has `retry_allowed=false`: there is no
automatic retry, fallback, role/model change, cleanup, or replacement worker.
A corrected task needs human authorization, a new attempt identity, a new
candidate, and a new READY dispatch.

`COMPLETED` means only that this bounded task and focused validation produced
the stated evidence. It is not Test Engineer acceptance, Gatekeeper approval,
promotion, commit, push, public export, or release.

## Boundary

Process-group containment is POSIX-specific; Windows and non-POSIX behavior are
outside this adapter contract. A global Codex skill symlink may make this file
visible to host-local sessions, but visibility is not activation and does not
guarantee that another host resolves or runs the adapter. The runner is
private to WYSY's Codex adapter and is not a public Coding Team export.
