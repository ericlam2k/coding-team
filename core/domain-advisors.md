# Domain Advisors — naming & activation

Talent-Career-Advisor in product-specific installs is one instance of a **general Domain Expert** pattern. In this framework the pattern is:

| | |
|---|---|
| **Template role** | `domain-advisor` |
| **Display name** | `[Domain]-Advisor` |
| **Instance canonical ID** | `{domain}-advisor` (kebab-case) |

## Naming convention

1. Human (or sprint brief) supplies a **Domain** label — one short noun/phrase.
2. Lead normalizes:
   - Display: `Title-Case` words joined with `-` + `-Advisor`  
     Examples: `Talent-Advisor`, `Strategic-Advisor`, `Security-Advisor`, `Legal-Advisor`
   - ID: lowercase kebab + `-advisor`  
     Examples: `talent-advisor`, `strategic-advisor`, `security-advisor`, `legal-advisor`
3. Strip suffixes the user already typed (`Advisor`, `Expert`, `Domain`) before appending `-advisor` once.
4. Record both display name and instance ID in the task brief.

**Valid:** `talent-advisor`, `strategic-advisor`, `clinical-advisor`  
**Invalid:** inventing `chief-of-staff`, `shadow-pm`, or a second Lead — those are not Domain Advisors.

## When to ask the user

Lead **must ask** when:

- Nature is Consult (or domain risk on N2/N5), and
- Specialty judgment is needed beyond PM / technical Advisor, and
- No domain is named in the sprint/batch brief

Ask once, short options (≤3 examples + free text). Do **not** assume Talent, Strategic, or any product-specific domain.

If the human says **skip** → do not spawn a Domain Advisor; continue with PM and/or technical Advisor only.

## Authority

| Peer | Owns |
|---|---|
| Product Manager | Product scope / acceptance |
| Advisor (`advisor`) | Pre-build **technical** verdict |
| **Domain Advisor** (`{domain}-advisor`) | Named **domain** trust/fairness/strategy/compliance/etc. |
| Contradictor | Challenge plan (technical or as briefed) |
| Gatekeeper | Post-build accept/block |

Domain Advisor is a **Consult peer** — not under PM, not under technical Advisor, not a Gatekeeper, no implementation.

## Mapping common aliases

| User says | Instance ID |
|---|---|
| Talent / Talent-Career / employment / hiring fairness | `talent-advisor` |
| Strategic / strategy / business strategy | `strategic-advisor` |
| Security / AppSec | `security-advisor` |
| Legal / compliance (non-binding; not a lawyer) | `legal-advisor` |
| Other clear domain word | `{that}-advisor` after normalize |
| Unclear | **Ask** — do not map |

## Brief requirements

Every Domain Advisor task brief must include:

```text
role_template: domain-advisor
instance_id: {domain}-advisor
display_name: [Domain]-Advisor
domain: <user-supplied>
question: <one bounded consult question>
evidence_paths: <paths or "none — ask Lead">
stop: no code; handoff only
```

## WIP

Domain Advisor counts toward WIP ≤ 2 like any other tool-using specialist.
