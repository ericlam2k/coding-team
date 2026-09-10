---
name: qa-evidence-enforcement
description: Validate bounded QA evidence and promotion readiness for Coding Team batches with mutation, state, ambiguity, regression, integration, or fix-trial risk. Use after Test Engineer execution and before Gatekeeper review; do not use for ordinary low-risk tasks without a QA-required trigger.
---

# QA Evidence Enforcement

Use this skill only for the **Risky** QA mode: a batch marked
`qa_required=true` or `qa_mode=bounded`. Normal changes follow
`$CODING_TEAM_ROOT/core/qa-operating-model.md` without this overlay. The core
policy and validator are the authority; this skill does not create roles,
change WIP, fix product code, or approve release.

The validator is an internal Test Engineer command. It is not a role or a
separate approval gate.

## Workflow

1. Resolve `CODING_TEAM_ROOT` from the host adapter, then read the batch brief,
   frozen scenario matrix, relevant contract/ADR, and
   `$CODING_TEAM_ROOT/core/qa-operating-model.md`. Do not resolve the core file
   relative to the installed skill symlink.
2. Set the QA timebox before starting execution: target **120 seconds**, hard
   stop **240 seconds**. Select only the layers and case references admitted by
   the batch; never turn a bounded pass into a repository-wide test run.
3. Confirm the scenario baseline is `Frozen for build`. A `Draft` baseline is
   design input only and cannot support promotion.
4. Confirm the selected test layers and explicit `N/A` reasons. Do not create
   entries for unaffected layers or run the whole repository by default.
5. Run the selected cases once. At the soft limit, stop scheduling new cases;
   at the hard limit, stop/cancel the active command and record a bounded
   `BLOCKED` result with `TIMEOUT` or `CANCELLED`, the stop reason, evidence
   paths, and one next action. Do not wait for a hung dependency or auto-retry.
6. After the complete validation pass, record every in-scope finding before any
   correction. Do not dispatch or apply a product fix during that pass.
7. Classify findings only as `PRODUCT_DEFECT`, `TEST_CONTRACT_DEFECT`,
   `ENVIRONMENT_DEFECT`, `TOOL_TRANSPORT_DEFECT`, or `UNKNOWN`.
8. Record the correlation result, demonstrated root cause or explicit
   no-shared-cause result, corrective Batch reference, and regression references.
9. Record the exact current candidate identity from
   `$CODING_TEAM_ROOT/core/qa-operating-model.md`: either the validated commit
   with a clean working tree, or closed manifest-bound `DIRTY` evidence. The
   latter binds the validated HEAD commit, manifest, candidate tree, working
   tree, and per-file hashes and requires repository revalidation; a commit
   alone is insufficient.
10. Run the repository validator:

   ```bash
   ruby scripts/validate-qa-evidence.rb path/to/qa-evidence.json --repo .
   ```

11. Return `PASS`, `FAIL`, or `BLOCKED` with the command output and evidence
   paths. A failed validator is not an invitation to patch the product or
   weaken the manifest.

## Promotion rules

Promotion is valid only when all of these are true:

- frozen scenario baseline;
- TE result `PASS`;
- every mandatory layer `PASS`, or `N/A` with a reason;
- regression result `PASS`;
- all findings collected and classified;
- correlation complete;
- confirmed defects linked to a regression case or corrective Batch;
- Gatekeeper decision is not started until this evidence is accepted;
- Code Reviewer, TE, QA-validator, and Gatekeeper reviewed identity all match
  the exact current candidate identity; commit mode retains the reviewed-commit
  equality check, while manifest mode requires matching identity evidence and
  repository revalidation;
- human approval exists when a human gate is required.

`FAIL`, `BLOCKED`, `TIMEOUT`, `REVISE`, stale evidence, missing evidence,
identity mismatch, failed repository revalidation, or dirty evidence without a
valid closed manifest stops promotion. A timeout is a valid stop record, not a
pass: Gatekeeper must not start, and the Lead must queue one smaller follow-up
or ask the human. Do not auto-retry.

## Scope boundary

- `test-scenarios` designs cases before build.
- `web-testing` executes tests where applicable.
- This skill validates evidence and promotion readiness.
- `debugging` or `root-cause-tracing` may be named for failure analysis, but
  this skill never replaces those methods or changes code.
- The validator checks the declared candidate identity and current repository
  evidence at validation time; it cannot claim to observe arbitrary editor
  writes during an active test run unless the host adapter provides that
  instrumentation.
