# Project roles

Project roles are domain specialists installed for one product. They are not
generic Coding Team roles and must not replace Lead, System Architect, Advisor,
Contradictor, Test Engineer, or Gatekeeper.

## Loading rule

Lead loads a project role only when the concern requires domain meaning that
technical roles cannot safely infer. The role returns a compact domain
decision/acceptance handoff; it does not implement application code or approve
release.

## Registered roles

| Role ID | Domain | Use when |
|---|---|---|
| `domain-expertise-advisor` | Installed project domain | Domain terminology, stakeholder boundaries, customary workflow, operational acceptance, trust/fairness, or real-world failure modes are unclear |

Project roles use the same WIP ≤2 and serial consultation rules as core roles.
