# Task brief

> Run prompt body ≤ **250 words**. Keep ownership exclusive.

## Identity

- **Task ID:**
- **Batch ID:**
- **Role ID:** (canonical only)
- **Nature:**
- **Tier planned → actual:**
- **Stage:** pre-build | build | code-review | targeted-TE | gatekeeper | docs
- **`timing_profile_ref`:** `../adaptive-timing.md` (approved versioned profile or labeled fallback)
- **Timing profile:** `version=`; `provenance=`; `status=` (`APPROVED` | `FALLBACK` | `STALE` | `INVALID`)

## Objective

- **One-sentence goal:**
- **Done when:**

## Scope

- **Owned files (exclusive):**
- **Read-only inputs:**
- **Do not touch:**

## Lead request-shaping note (use only when needed)

Use this compact planning note when the request is broad, ambiguous, or needs
splitting; omit it for an already spec-ready Task. It records the Lead's
selection and does not change the existing Sprint → Batch → Task flow.

- **Disposition:** `SINGLE` | `SPLIT` | `CLARIFY` | `MEASURE` | `BLOCK`
- **Selected slice:** `SINGLE` / `SPLIT`: exactly one dependency-safe slice for
  this brief; `CLARIFY` / `MEASURE` / `BLOCK`: `NONE`
- **Queued remainder:** owner + prerequisite + state for later slices, or `NONE`
- **Evidence / reversible assumption:** pointer, owner, and undo condition
- **Human question:** `NONE`, or one plain-language question only when a
  product or irreversible choice changes the slice

## Skills (named or none)

- 

## Constraints

- **WIP slot:** 1 of 2
- **Depends on:**
- **Stop / escalate if:**

## Evidence route (when applicable)

- **Candidate / deterministic checks / Code Reviewer artifact:**
- **TE trigger and targeted packet, or direct-route rationale:**
- **Gatekeeper inputs / unresolved `BLOCKER` guard:**

## Size budget

- **Expected active run:** `T_target=`; `T_hard=`; `T_reserve=` (seconds; resolved from the timing profile)
- **Independent concerns:** 1
- **Acceptance artifact:**
- **Immediate handoffs allowed:** 1; a second means split again
- **Checkpoint trigger:** `T_checkpoint`, missing artifact, or any width limit crossed

## Workload admission (required before dispatch)

- **Resolved timing bounds:** `T_target=`; `T_checkpoint=`; `T_hard=`;
  `T_reserve=`; `max_hard_cap_s=` (seconds; from `timing_profile_ref`)
- **p95 setup inputs:** `policy=`; `memory=`; `migration=`;
  `repository-bootstrap=`; total `T_setup,p95=`
- **Other p95 inputs:** `mutation-unit=`; `validation-command=`; `handoff=`
- **Input evidence:** each duration is `MEASURED` | `ESTIMATED` | `UNKNOWN`
  with source, class, and conditions; `MEASURED` needs a receipt;
  `ESTIMATED` or mandatory `UNKNOWN` → `MEASURE` and no dispatch
- **Candidate boundary:** `candidate_changed_paths=`; candidate-wide identity
  receipt; `prior_hard_stop=` (`true` → `BLOCK`)
- **Calculation:** `T_plan = T_setup,p95 + ΣT_mutation-unit,p95 +
  ΣT_validation-command,p95 + T_handoff,p95`; concurrent critical-path pricing
  requires frozen scenarios, disjoint resources, and independence evidence
- **Admission action:** `ADMIT` | `MEASURE` | `SPLIT` | `BLOCK`, applying
  [`adaptive-timing.md`](../adaptive-timing.md) in its stated order
- **Fresh-bootstrap decision:** if measured setup consumes the useful window,
  block an unchanged fresh route; reuse valid same-task context only with a
  material scope/dependency/tool-route/environment delta, or pre-resolve setup
  and shrink the next Task. Never retry or model-hop to reset the clock.

## Run prompt

```text
(role + goal + owned paths + skills + stop conditions; ≤250 words)
```

## Output

- Handoff using `templates/handoff.md` (≤150 words)
