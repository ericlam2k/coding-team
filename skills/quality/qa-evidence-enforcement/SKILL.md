---
name: qa-evidence-enforcement
description: Validate bounded QA evidence and promotion readiness for Coding Team batches with mutation, state, ambiguity, regression, integration, or fix-trial risk. Use after Test Engineer execution and before Gatekeeper review; do not use for ordinary low-risk tasks without a QA-required trigger.
---

# QA Evidence Enforcement

Use this skill as the Test Engineer evidence-control step for a batch marked
`qa_required=true` or `qa_mode=bounded`. The core policy and validator are the
authority; this skill does not create roles, change WIP, fix product code, or
approve release.

## Workflow

1. Read the batch brief, frozen scenario matrix, relevant contract/ADR, and
   [core/qa-operating-model.md](../../../core/qa-operating-model.md).
2. Confirm the scenario baseline is `Frozen for build`. A `Draft` baseline is
   design input only and cannot support promotion.
3. Confirm the required test layers and explicit `N/A` reasons. Do not require
   every layer for every task; use the trigger flags in the manifest.
4. After the complete validation pass, record every in-scope finding before any
   correction. Do not dispatch or apply a product fix during that pass.
5. Classify findings only as `PRODUCT_DEFECT`, `TEST_CONTRACT_DEFECT`,
   `ENVIRONMENT_DEFECT`, `TOOL_TRANSPORT_DEFECT`, or `UNKNOWN`.
6. Record the correlation result, demonstrated root cause or explicit
   no-shared-cause result, corrective Batch reference, and regression references.
7. Record the exact `validated_commit` and require a clean working tree.
8. Run the repository validator:

   ```bash
   ruby scripts/validate-qa-evidence.rb path/to/qa-evidence.json --repo .
   ```

9. Return `PASS`, `FAIL`, or `BLOCKED` with the command output and evidence
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
- Gatekeeper reviewed commit equals the TE validated commit;
- human approval exists when a human gate is required.

`FAIL`, `BLOCKED`, `REVISE`, stale evidence, missing evidence, dirty-tree
evidence, or commit mismatch stops promotion. Do not auto-retry.

## Scope boundary

- `test-scenarios` designs cases before build.
- `web-testing` executes tests where applicable.
- This skill validates evidence and promotion readiness.
- `debugging` or `root-cause-tracing` may be named for failure analysis, but
  this skill never replaces those methods or changes code.
- The validator checks commit identity and promotion evidence; it cannot claim
  to observe arbitrary editor writes during an active test run unless the host
  adapter provides that instrumentation.
