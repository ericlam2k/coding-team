# QA Operating Model (Hybrid)

This is the active Coding Team QA policy. The previous layered operating model
is archived at
`docs/archive/qa-operating-model-pre-hybrid-29311de.md`; do not load it by
default.

Use the smallest flow that gives reliable evidence. Keep WIP ≤2, disjoint write
scopes, and Test Engineer (TE) → Gatekeeper (GK) sequential. Do not create a
standing QA meeting or a second router.

## Mode selection

Use **Normal** mode by default. Escalate to **Risky** mode when any of these
are present: mutation or state transition, replay/currentness, unclear user or
domain meaning, shared contract, external integration, auth/privacy/security,
migration/rollback, material regression risk, repeated failure, or a second
failed fix attempt.

If a normal task hits the same failure twice or reveals one of those triggers,
stop the normal loop and restart it as a Risky batch. Do not keep patching
forward.

## Normal changes

1. Agree the expected behavior and scope.
2. Define key user-observable test cases, including the important negative or
   edge case.
3. Implement or fix the smallest boundary.
4. Run the selected tests.
5. Log each defect with expected/actual result and evidence.
6. Retest the corrected case.
7. Run suitable affected regression, not the whole repository by default.
8. For a material batch, obtain fresh TE evidence, then one sequential GK
   decision. Low-risk local work may close with its recorded check when the
   batch does not require independent TE/GK review.

PM, Domain Advisor, Architect, or Contradictor input is conditional: consult
only when that decision can change the expected behavior, contract, or risk.

## Risky or confusing changes

1. Freeze the test batch before implementation. Resolve user/domain meaning
   first; select only the affected test layers and cases.
2. Run the complete frozen batch once before patching. Do not dispatch a fix
   while that validation pass is active.
3. Log all failures with scenario, expected/actual result, evidence, and
   classification.
4. Correlate findings once. Group only failures with a demonstrated shared
   cause; do not cluster by symptom wording alone.
5. Admit one controlled corrective Batch with exclusive files.
6. Run a fresh TE pass for failed cases, affected regression, and relevant
   negative/adversarial cases.
7. Promote only with complete evidence and TE → GK approval. Human approval
   remains required for production, irreversible, privacy/legal, or other
   human-gated actions.

## Timebox and stop rules

For Risky batches, target 120 seconds and hard-stop at 240 seconds. At the
target, stop scheduling new cases. At the hard stop, cancel the active command
and record `BLOCKED` with the timeout reason, evidence collected, and one next
action. Do not auto-retry, patch during the pass, or start GK on incomplete
evidence.

`FAIL`, `BLOCKED`, stale evidence, dirty-tree evidence, commit mismatch, or GK
non-approval stops promotion and returns control to Lead/human decision.

## Minimum evidence

Normal mode records: expected behavior, selected cases, commands/results,
defects, retest result, affected regression result, and next action or stop
reason.

Risky mode additionally records: frozen baseline, selected layers/cases, all
findings, correlation/root cause, corrective Batch, fresh TE result, regression
result, exact validated commit, and GK decision.
