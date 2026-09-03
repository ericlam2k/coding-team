# QA Operating Model

This is the active Coding Team QA policy. The previous layered operating model
is archived at
`docs/archive/qa-operating-model-archive-29311de.md`; do not load it by
default.

Resolve timing from the approved profile in [`adaptive-timing.md`](adaptive-timing.md):
use `T_target`, `T_checkpoint`, `T_hard`, and `T_reserve`, with
`T_hard <= max_hard_cap_s`. Use the smallest reliable evidence scope, WIP ≤2
ordinary plus at most one read-only, non-authoritative supervisor relay (total
child lanes ≤3 only when that relay is admitted), disjoint writers, and one
quality chain:

```text
frozen candidate → deterministic checks → Code Reviewer → conditional TE → Gatekeeper
```

Code Reviewer owns bounded diff/static inspection and the risk route. Test
Engineer (TE) owns executable behavior; it does not repeat broad static review.
Gatekeeper (GK) is always the final acceptance authority. Candidate mutation
invalidates prior Reviewer and TE evidence.

## Canonical Reviewer route

This section is the sole source for Reviewer verdict routing and post-review
TE triggers. Adapters, role cards, and other core documents link here rather
than restate the decision rules.

Apply the route in this order for the same immutable candidate:

1. An unresolved `BLOCKER` or Reviewer `BLOCK` stops for Lead/human decision;
   Gatekeeper cannot accept it.
2. Reviewer `REVISE` returns the candidate to its named implementation owner
   for correction. Bind a new candidate, rerun deterministic checks, and
   obtain a fresh review before any further route.
3. Reviewer `ESCALATE_TO_TEST_ENGINEER` routes targeted TE.
4. Reviewer `PASS` or `PASS_WITH_NOTES` routes directly to Gatekeeper only
   when Lead and Reviewer record `LOW` risk, deterministic evidence is
   complete and passing, candidate/evidence identity is exact, no trigger
   below applies, and the direct-route rationale is recorded.
5. Every other eligible case routes targeted TE. Unsupported Reviewer
   verdicts stop at Lead; they are not translated into acceptance.

TE is required when runtime evidence is explicit in acceptance, deterministic
checks fail or are insufficient, or the change involves:

- frontend/backend/API/database integration or a shared/public contract;
- auth, authorization, session, privacy, security, or financial behavior;
- migration, transformation, transaction, state, concurrency, recovery, or idempotency;
- external services, jobs, queues, cache, retry, timeout, or environment/deploy config;
- browser, responsive, accessibility, interaction, or performance behavior;
- a production regression, fix after failure, or release-impacting risk; or
- a Gatekeeper or repository-policy requirement, including
  `qa_required=true` or `qa_mode=bounded`.

Every TE trigger needs provenance from the admitted Task or Batch, a named
higher-authority policy, or an observed Reviewer finding. Code Reviewer must
not infer `qa_required`, `qa_mode`, shared/public-contract impact, or runtime
risk merely because a framework file changed. A low-risk deterministic prompt,
parser, or internal tool change with complete focused checks may take the
direct route. If runtime evidence is still needed, Reviewer must return
`ESCALATE_TO_TEST_ENGINEER` and name the unresolved observable behavior.

Non-low risk, missing, legacy, mismatched, disputed, or uncertain input routes
targeted TE. TE and Gatekeeper remain sequential whenever TE runs. Gatekeeper
is always final and may challenge a direct-route rationale.

## Candidate identity and currentness

A closed candidate uses one identity mode:

- **Commit mode:** the validated commit with a clean working tree.
- **Manifest mode:** the validated HEAD commit plus closed manifest-bound
  `DIRTY` evidence whose manifest and per-file digests are revalidated.

The Code Reviewer artifact, TE report, triggered QA-validator result, and
Gatekeeper reviewed identity must all bind the exact current candidate. Any
candidate-byte or identity mutation makes prior evidence stale; freeze and
validate the new identity before Gatekeeper starts.

## Targeted TE packet and report

Lead sends only changed behavior, executable acceptance criteria, candidate and
components, Reviewer findings/residual risk, exact triggers, environment,
relevant commands, exclusions, and maximum scope. TE starts with the smallest
relevant test set and widens only after a failure, shared-contract evidence,
broader regression evidence, or an explicit policy requirement; record why.

TE reports the exact candidate identity used, scope, environment/config,
commands/procedures, pass/fail evidence, covered and uncovered acceptance
criteria, changed tests, residual risk, and `PASS`, `FAIL`, or `BLOCKED`.
Summarize logs and cite artifacts. When `qa_required=true` or `qa_mode=bounded`,
run the bounded QA evidence validator after TE and before GK.

## Mode selection

Use **Normal** mode by default. Escalate to **Risky** mode when any of these
are present: mutation or state transition, replay/currentness, unclear user or
domain meaning, shared contract, external integration, auth/privacy/security,
migration/rollback, material regression risk, repeated failure, or a second
failed fix attempt.

## Normal changes

1. Agree expected behavior, scope, and the important negative/edge case.
2. Implement the smallest boundary; freeze the candidate and deterministic evidence.
3. Obtain one Code Reviewer verdict and route.
4. Run targeted TE only when required, then one sequential GK decision.

Consult PM, Domain Advisor, Architect, or Contradictor only when that decision
can change behavior, contract, or risk.

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
6. Freeze the corrected candidate, rerun deterministic checks and Code Reviewer,
   then run targeted TE for failed, affected-regression, and relevant negative
   cases.
7. Promote only with complete evidence, validator when triggered, and TE → GK
   approval. Human approval remains required for production, irreversible,
   privacy/legal, or other human-gated actions.

## Timebox and stop rules

Use `T_target` and hard-stop at `T_hard`, preserving `T_reserve` for handoff
and evidence. At `T_target`, stop scheduling new cases. At `T_checkpoint`
without a complete artifact, emit a checkpoint; at `T_hard`, cancel the active
command and record `BLOCKED` with the timeout reason, evidence collected, and
one next action. A Task is too wide when it has multiple owners/independent
concerns, non-disjoint writes, no single artifact, or cannot fit the 250-word
run-prompt / 150-word handoff caps. Do not auto-retry, patch during the pass,
leave work frozen, or start GK on incomplete evidence.

`FAIL`, `BLOCKED`, stale or mismatched evidence, unresolved `BLOCKER`, validator
failure, or GK non-approval stops promotion and returns control to Lead/human.

## Minimum evidence

Normal mode records expected behavior, candidate identity, selected checks and
results, Reviewer artifact/route, TE report or direct-route rationale, defects,
retest, affected regression, validator result when triggered, GK decision, and
next action or stop reason. Risky mode additionally records the frozen baseline,
all findings, root-cause correlation, corrected candidate identity, and every
TE scope expansion.
