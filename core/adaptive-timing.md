# Adaptive timing policy (V1)

## Use and authority

This platform-neutral policy bounds work for an app/profile and environment.
Explicit app or user input is authoritative; otherwise use versioned
recommendations. Monitor may observe and propose only. The app owner must
approve any durable profile change.

## Profile and invariants

Each profile records `app_id`, `class`, `target_s`, `checkpoint_s`,
`hard_stop_s`, `reserve_s`, `max_hard_cap_s`, `initial_target_s`,
`min_success_samples`, `alpha`, `blend_weight`, `margin`, `max_step_ratio`,
`calibrated_at`, `valid_until`, `environment_fingerprint`, `provenance`,
`version`, and `approved_by`. Bounds must be positive,
`target < checkpoint < hard_stop`, `hard_stop_s <= max_hard_cap_s`, and
`reserve < hard_stop-target`; `max_hard_cap_s` is required. The class/version,
app/environment, approval (`APPROVED`), and validity must match. Otherwise
select the versioned fallback and state remediation. The fallback may preserve
a legacy cap; no cap is a universal constant.

Resolve `T_target = target_s`, `T_checkpoint = checkpoint_s`,
`T_hard = hard_stop_s`, and `T_reserve = reserve_s` from that approved profile
or labeled fallback.

## Editable V1 recommendation

Defaults are recommendations, not invariants: `initial_target_s=90`,
`min_success_samples=5`, `alpha=0.3`, `blend_weight=0.5`, `margin=1.25`, and
`max_step_ratio=0.2`. Every value remains app-configurable.

## Request-to-time admission

Before dispatch, price all required work using same-class, same-environment p95
durations. Each input is `MEASURED`, `ESTIMATED`, or `UNKNOWN` and records its
source, class, and conditions. Setup includes the policy, memory, migration,
and repository bootstrap that the route requires:

`T_setup,p95 = T_policy,p95 + T_memory,p95 + T_migration,p95 + T_repo-bootstrap,p95`

`T_plan = T_setup,p95 + ΣT_mutation-unit,p95 + ΣT_validation-command,p95 + T_handoff,p95`

The admission envelope also records `candidate_changed_paths` and
`prior_hard_stop`. A scoped Task must not hide candidate-wide path verification
inside its validation list; precompute that identity as a separate receipt or
split the Task. Every `MEASURED` duration names its evidence reference.
`ESTIMATED` time returns `MEASURE`, never `ADMIT`. `prior_hard_stop=true`
means the same material route already stopped and returns `BLOCK`; do not
spend another worker run on that route. It is not an objective-wide flag.

Price concurrent branches by their critical-path maximum only when scenarios
are frozen, resources are disjoint, and independence evidence is recorded;
otherwise price them sequentially. Never price time from test count.

Apply `ADMIT|MEASURE|SPLIT|BLOCK` in this order:

1. Any mandatory `UNKNOWN` input returns `MEASURE`; do not dispatch.
2. Validation beyond `T_hard - T_reserve` or a failed prerequisite check
   returns `BLOCK`.
3. `T_plan <= T_target` returns `ADMIT`; otherwise return `SPLIT`.
4. Atomic measured-p95 work may exceptionally return `ADMIT` only when
   `T_plan + T_reserve < T_hard` and `T_hard <= max_hard_cap_s`.

### Fresh-bootstrap protection

Setup has consumed the useful window when its measured elapsed time leaves
less than the priced mutation, validation, and handoff work before `T_target`.
After that condition, an unchanged fresh route is `BLOCK`; do not retry it or
hop models. Either reuse valid same-task context with a material delta to
scope, dependency, tool route, or environment, or pre-resolve required setup
in a bounded `MEASURE` task and shrink the subsequent task. Reuse is allowed
only while task identity, scope, permissions, policy, and evidence remain
current; otherwise checkpoint and return to Lead.

### Hard-stop reconciliation (timebounce)

A hard stop ends one execution route, not the authorized objective. Apply this
sequence before asking the human or allocating more work:

1. **Observe:** poll the live handle or verify terminal state. An observation
   timeout alone is not a terminal worker result.
2. **Reconcile:** inspect the declared artifact paths and classify the route as
   `COMPLETE`, `PARTIAL`, or `NO_PROGRESS`; never discard usable partial work.
3. **Record:** write one structured checkpoint containing dispatch identity,
   completed work, remaining work, evidence, and the stop cause.
4. **Reduce:** manually validate the smallest remaining step, then form one
   smaller single-owner Task with pre-resolved inputs and structured output.
5. **Reprice:** record the material delta—scope, context mode, dependency,
   validation path, tool route, or environment. Set `prior_hard_stop=false`
   only for that demonstrably changed route; the unchanged route remains true
   and blocked.
6. **Escalate selectively:** ask the human only when continuation changes
   product behavior, scope, provider authorization, risk acceptance, or an
   existing human gate, or when no material route remains.

This follows the Karpathy-style operating pattern used by this repository:
validate manually before automating, track state in files, require structured
outputs, estimate cost first, and start with one worker before adding lanes.
It is controlled decomposition, never an automatic retry or model hop.

## Calculation and limits

For a successful same-class, same-environment duration `d_n`:

`active_cap_s = min(hard_stop_s, max_hard_cap_s) - reserve_s`

`E_n = alpha*d_n + (1-alpha)*E_(n-1)`

`R_raw = min(active_cap_s, ceil(blend_weight*target_s + (1-blend_weight)*margin*E_n))`

Rate-limit `R_raw` to the configurable `max_step_ratio` interval around the
prior approved recommendation, then cap it at `active_cap_s`. Before
`min_success_samples`, show `min(initial_target_s, active_cap_s)`. EWMA uses
exponential weighting because it adapts to recent evidence without discarding
history. Configuration is preferred to universal constants because workload
and environment differ.

## Readiness, timeout evidence, and admission

Readiness requires a valid approved profile, matching context, and sufficient
successful samples or an explicitly labeled cold-start recommendation. Failed
or timed-out runs never enter the successful-duration EWMA because their
completion time is unknown; keep these right-censored outcomes separate.
Monitor records count, denominator, failure rate, provenance, profile/version,
threshold, phase, plan/elapsed time, completed/pending work,
environment/resources, and owner/action, returning `SPLIT/REVIEW` evidence.
At `T_hard`, stop safely without automatic retry; both active and maximum caps
apply. Pre-dispatch actions are `ADMIT|MEASURE|SPLIT|BLOCK`; post-dispatch
outcomes are `CHECKPOINT|REVIEW|STOP`.

## Presentation and migration

Plain UI/docs highlight the editable recommendation and reason, decision,
remaining bound, fallback/remediation, and next action. Expert presentation
adds parameters, samples, provenance, caps, failure rate, profile/version,
validation/staleness, `T_plan`, and comparisons.

Preserve fixed values as versioned recommendations; add read-only evidence,
shadow-compare, then enable approved profiles. Store no payloads.
Security/privacy, availability, scale, and retention require separate
verification. Durable changes require explicit approval. This policy is
independent of operating system, runtime, or provider.
