# Adaptive timing policy (V1)

## Use and authority

This platform-neutral policy bounds work for an app/profile and environment. Explicit app or user input is authoritative; otherwise use versioned recommendations. Monitor may observe and propose only. The app owner must approve any durable profile change.

## Profile and invariants

Each profile records `app_id`, `class`, `target_s`, `checkpoint_s`, `hard_stop_s`, `reserve_s`, `max_hard_cap_s`, `initial_target_s`, `min_success_samples`, `alpha`, `blend_weight`, `margin`, `max_step_ratio`, `calibrated_at`, `valid_until`, `environment_fingerprint`, `provenance`, `version`, and `approved_by`. Bounds must be positive, `target < checkpoint < hard_stop`, `hard_stop_s <= max_hard_cap_s`, and `reserve < hard_stop-target`; `max_hard_cap_s` is required. The class/version, app/environment, approval (`APPROVED`), and validity must match. Otherwise select the versioned fallback and state remediation. The fallback may preserve a legacy cap; no cap is a universal constant.

## Editable V1 recommendation

Defaults are recommendations, not invariants: `initial_target_s=90`, `min_success_samples=5`, `alpha=0.3`, `blend_weight=0.5`, `margin=1.25`, and `max_step_ratio=0.2`. Every value remains app-configurable.

## Calculation and limits

For a successful same-class, same-environment duration `d_n`:

`active_cap_s = min(hard_stop_s, max_hard_cap_s) - reserve_s`

`E_n = alpha*d_n + (1-alpha)*E_(n-1)`

`R_raw = min(active_cap_s, ceil(blend_weight*target_s + (1-blend_weight)*margin*E_n))`

Rate-limit `R_raw` to the configurable `max_step_ratio` interval around the prior approved recommendation, then cap it at `active_cap_s`. Before `min_success_samples`, show `min(initial_target_s, active_cap_s)`. EWMA uses exponential weighting because EWMA gives recency-weighted adaptation without discarding history. Configuration is preferred to universal constants because workload and environment differ.

## Readiness, timeout evidence, and admission

Readiness requires a valid approved profile, matching context, and sufficient successful samples (or an explicitly labeled cold-start recommendation). Failed or timed-out runs never enter the successful-duration EWMA: their completion time is unknown, so right-censored outcomes must remain separate. Monitor records count, denominator, failure rate, provenance, profile/version, threshold, phase, elapsed/completed/pending work, environment/resources, and owner/action, returning `SPLIT/REVIEW` evidence. At hard stop, stop safely without automatic retry; both active and maximum caps apply. Pre-dispatch actions are `ADMIT|MEASURE|SPLIT|BLOCK`; post-dispatch runtime/Monitor outcomes are `CHECKPOINT|REVIEW|STOP`.

## Presentation and migration

Plain UI/docs highlight the editable recommendation and reason, decision, remaining bound, fallback/remediation, and next action. Expert presentation adds parameters, samples, provenance, caps, failure rate, profile/version, validation/staleness, `T_plan`, and comparisons.

Preserve fixed values as versioned recommendations; add read-only evidence, shadow-compare, then enable approved profiles. Store no payloads. Security/privacy, availability, scale, and retention require separate verification. Durable changes require explicit approval because approval preserves auditability and reversibility. This policy is independent of operating system, runtime, or provider.
