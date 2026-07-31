# Roles

Canonical IDs are stable labels. Adapters may also record a runtime subagent UUID for resume — keep both.

| Canonical ID | Answers | Access |
|---|---|---|
| `lead` | What is the plan and who owns what? | Coordinate only; no builder-owned implementation by default |
| `product-manager` | Is this the right product scope? | Consult; no implementation |
| `advisor` | What should we do technically? | Read-only pre-build |
| `contradictor` | Why might the plan be wrong? | Read-only pre-build; serial with Advisor |
| `domain-advisor` | What does the **named domain** say? | Consult peer; template → `{domain}-advisor` |
| `investigator` | What does the repo say? | Read-only map |
| `backend-engineer` | Server / API / data change | Scoped writes |
| `frontend-ux-lead` | UX contract / design review | Read + scoped writes when assigned |
| `frontend-builder` | UI implementation | Scoped writes |
| `test-engineer` | Does evidence prove it? | Tests / fixtures; independent of builders |
| `docs-steward` | What should humans read later? | Docs writes only |
| `gatekeeper` | Can we accept this as done? | Read-only decision after TE |

Role cards: [`core/roles/`](../core/roles/).  
Domain Expert pattern: [`core/domain-advisors.md`](../core/domain-advisors.md).

## Domain Expert → `[Domain]-Advisor`

There is **no** fixed Talent-Career role in this framework. When specialty judgment is needed:

1. Lead asks the human which **domain** (unless already in the brief).
2. Map to display `[Domain]-Advisor` and id `{domain}-advisor` (e.g. `Talent-Advisor` / `talent-advisor`, `Strategic-Advisor` / `strategic-advisor`).
3. Load `core/roles/domain-advisor.md` with that instance id in the brief.

Domain Advisor is a peer to PM — not under PM or technical Advisor; no implementation; no Gatekeeper power.

## Authority rules

- Only **Lead** spawns, sequences, cancels, or reassigns specialists.
- Specialists return a handoff; they do not manage teammates.
- Unknown labels map to the closest predefined role **or** Domain Advisor instance. If none fits → `HUMAN_DECISION_REQUIRED`. Do not invent a new role family.
- Prefer different model family (or effort + fresh subagent) for Contradictor vs Advisor and Gatekeeper vs implementer.

## Skill pointers (by role)

See the coverage matrix in [skills.md](skills.md). Cards name exact paths under `skills/`.
