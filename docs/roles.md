# Roles

Canonical IDs are stable labels. Adapters may also record a runtime subagent UUID for resume — keep both.

| Canonical ID | Answers | Access |
|---|---|---|
| `lead` | What is the plan and who owns what? | Coordinate only; no builder-owned implementation by default |
| `product-manager` | Is this the right product scope? | Consult; no implementation |
| `advisor` | What should we do technically? | Read-only pre-build |
| `contradictor` | Why might the plan be wrong? | Read-only pre-build; serial with Advisor |
| `investigator` | What does the repo say? | Read-only map |
| `backend-engineer` | Server / API / data change | Scoped writes |
| `frontend-ux-lead` | UX contract / design review | Read + scoped writes when assigned |
| `frontend-builder` | UI implementation | Scoped writes |
| `test-engineer` | Does evidence prove it? | Tests / fixtures; independent of builders |
| `docs-steward` | What should humans read later? | Docs writes only |
| `gatekeeper` | Can we accept this as done? | Read-only decision after TE |

Role cards: [`core/roles/`](../core/roles/).

## Authority rules

- Only **Lead** spawns, sequences, cancels, or reassigns specialists.
- Specialists return a handoff; they do not manage teammates.
- Unknown labels map to the closest predefined role by capability. If none fits → `HUMAN_DECISION_REQUIRED`. Never invent a role.
- Prefer different model family (or effort + fresh subagent) for Contradictor vs Advisor and Gatekeeper vs implementer.

## Skill pointers (by role)

See the coverage matrix in [skills.md](skills.md). Cards name exact paths under `skills/`.
