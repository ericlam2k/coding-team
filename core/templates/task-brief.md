# Task brief

> Run prompt body ≤ **250 words**. Keep ownership exclusive.

## Identity

- **Task ID:**
- **Batch ID:**
- **Role ID:** (canonical only)
- **Nature:**
- **`quantized_class`:** `Q0` | `Q1` | `Q2` | `Q3` | `Q4`
- **`context_level`:** `C0` | `C1` | `C2` | `C3` | `C4` | `C5`
- **`context_budget_tokens`:** nonnegative integer
- **`model_tier`:** `NONE` | `0` | `1-build` | `1-validate` | `2` | `3` (abstract only)
- **`escalation_rules`:** explicit escalation and stop conditions
- **`quantization_status`:** `ROUTED` | `BLOCKED`
- **`quantization_confidence`:** `HIGH` | `MEDIUM` | `LOW`
- **`quantization_evidence_ref`:** input digest and evidence reference

Lead first resolves nature, canonical role, and the minimum abstract model tier. The dependency-free quantizer may raise that floor but never lower it; only afterward may the adapter map the model pool. Q0 uses no model. Context overflow returns compress/checkpoint and cannot cause a model hop.

Legacy briefs remain `UNSPECIFIED`; every new/corrected brief requires these fields or a `BLOCKED` quantization receipt.
- **Tier planned → actual:**
- **`execution_scope`:** one bounded verb; named paths, query, or source set; output artifact; explicit exclusions
- **`reasoning_depth`:** `MECHANICAL` | `RECONCILE` | `JUDGMENT`
- **`enumeration_required`:** `true` | `false`
- **`synthesis_input_ref`:** completed Investigator handoff/evidence path | `NONE`
- **`timing_profile_ref`:** `../adaptive-timing.md` (versioned profile or labeled fallback)
- **Timing profile:** `version=`; `provenance=`; `status=` (`APPROVED` | `FALLBACK` | `STALE` | `INVALID`)

## Objective

- **One-sentence goal:**
- **Done when:**

## Scope

- **Task scope:** `frontend` | `backend` | `cross-layer` | `ux-contract` | `none`
- **Owned files (exclusive):**
- **Owned integration seam (if this task carries the FIO overlay):**
- **FIO overlay:** `this task` | `none` — never create a separate FIO task
- **Read-only inputs:**
- **Do not touch:**

New and corrected briefs must fill the four assignment fields. Legacy briefs
without them remain readable as `UNSPECIFIED`. Do not dispatch new
policy-sensitive enumeration until Lead materializes the fields. If
`enumeration_required=true`, name a separate `investigator` Task before
manager synthesis.

## Skills (named or none)

-

## Constraints

- **WIP slot:** 1 of 2
- **Depends on:**
- **Stop / escalate if:**

## Size budget

- **Expected active run:** `T_target=`; `T_hard=`; `T_reserve=` (seconds; resolved from the timing profile)
- **Independent concerns:** 1
- **Acceptance artifact:**
- **Immediate handoffs allowed:** 1; a second means split again
- **Checkpoint trigger:** `T_checkpoint`, missing artifact, or any width limit crossed

For lookup work, also checkpoint before a second lookup session, source-set
expansion, a second follow-up, the 75% artifact review trigger, or unexplained
receipt growth without accepted evidence. Missing receipt data is
`TELEMETRY_UNAVAILABLE`, not zero. Context growth does not cause a model hop.

## Workload admission (required before dispatch)

- **Resolved timing bounds:** `T_target=`; `T_checkpoint=`; `T_hard=`; `T_reserve=`; `max_hard_cap_s=` (seconds; from `timing_profile_ref`)
- **Profile resolution:** version, provenance, and status must be recorded; otherwise use the versioned fallback and state remediation. The editable V1 `initial_target_s=90` recommendation may be supplied by the profile; it is not a template invariant.
- **p95 duration inputs:** `setup=`; `mutation-unit=`; `validation-command=`;
  `handoff=` — each must be labeled `MEASURED` | `ESTIMATED` | `UNKNOWN` and
  include its source, class, and conditions
- **Validation metadata:** named validation commands: `...`; expected case
  count: `...` (metadata only; never a time or admission threshold)
- **Calculation:** `SEQUENTIAL` with
  `T_plan = T_setup,p95 + ΣT_mutation-unit,p95 +
  ΣT_validation-command,p95 + T_handoff,p95`; or `CONCURRENT` only with
  frozen scenarios, disjoint resources, and recorded independence evidence,
  using the branch critical-path maximum
- **Admission action:** `ADMIT` | `MEASURE` | `SPLIT` | `BLOCK` — mandatory
  `UNKNOWN` → `MEASURE`; validation beyond `T_hard - T_reserve` or failed
  checks → `BLOCK`; otherwise compare `T_plan` with `T_target` and split when over
  target. Atomic measured-p95 work may exceptionally admit only when
  `T_plan + T_reserve < T_hard` and `T_hard ≤ max_hard_cap_s`
- **Retry delta:** scope, dependency, tool route, or environment change;
  unchanged retry → `BLOCK` | `SPLIT`

## Run prompt

```text
(role + goal + owned paths + skills + stop conditions; ≤250 words)
```

## Output

- Handoff using `templates/handoff.md` (≤150 words)
