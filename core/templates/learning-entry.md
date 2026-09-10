# Learning and distillation entry

Use one entry per material signal or explicitly grouped, demonstrated shared
cause. Keep it concise; link to evidence instead of pasting transcripts.

## Identity

- **Entry ID:**
- **Sprint / Batch / Task:**
- **Recorded at:**
- **Owner:** Lead
- **Status:** CANDIDATE | SUPPORTED | PROMOTED | RETEST | SUPERSEDED | CLOSED

## Capture

- **Source refs:** (run trace, TE evidence, Gatekeeper decision, cost/friction/graph refs)
- **Revision / commit:**
- **Scope and affected surface:**
- **Observed fact:**
- **Outcome / impact:**
- **Unknowns or unavailable telemetry:**

## Data boundary

- **Storage scope:** `LOCAL_ONLY`
- **Export status:** `NOT_REQUESTED`
- **Public safe:** `false`
- **Consent reference:** `null`
- **Redaction check:** `NOT_RUN`
- **Generic outcome only:** stage/status/aggregate duration or counts,
  evidence refs, cost provenance, and sanitized friction/lesson text
- **Prohibited:** source code, diffs, raw prompts/PRDs, transcripts, secrets,
  credentials, provider/account identifiers, PII, and private payloads

## Distillation

- **Claim class:** FACT | PATTERN | HYPOTHESIS | DECISION
- **Bounded lesson:**
- **Applicability / non-applicability:**
- **Supporting independent refs:**
- **Cheapest validation or falsifier:**
- **Confidence:** LOW | MEDIUM | HIGH — reason:

## Disposition

- **Destination:** NONE | HANDOFF | CHECKPOINT | SKILL | TEMPLATE | PROJECT_OVERLAY | ADAPTER | CORE_POLICY | ROUTING
- **Decision:** promote | keep local | retest | supersede | close
- **Human gate / approver / date:** (required for material promotion; `N/A` for local closure)
- **Validation result and refs:**
- **Owner and due/review date:**
- **Revalidation or expiry trigger:**

## Learning Review (derived, never authority)

- **Candidate confidence:** (0–100; show component calculation)
- **Confidence tier:** EXPERIMENTAL | PROBATION | TRUSTED | PROMOTION_CANDIDATE
- **Components:** outcome improvement / Gatekeeper impact / repeatability /
  evidence strength / sample size (30% / 25% / 20% / 15% / 10%)
- **Decay signal:** CURRENT | REVIEW_DUE | WEAKENED | CONTRADICTED | STALE
- **Decay reason and next review:**
- **Concern lenses:** technical / process / product / security — COVERED | PARTIAL |
  UNRESOLVED | CONTRADICTED | NOT_APPLICABLE
- **Promotion review:** pending | eligible | rejected | approved
- **Authority guard:** no source-skill edit, role/model route, stage advance,
  export, or policy promotion from this record alone

## Safety check

- [ ] No source code, diffs, secrets, credentials, raw private data, or unnecessary transcript content
- [ ] Fact is separated from interpretation and unknowns
- [ ] No cost/quality/model claim exceeds the available evidence
- [ ] Scope is narrower than or equal to the supporting evidence
- [ ] Contradicting or superseded claims are linked
