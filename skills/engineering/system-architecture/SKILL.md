---
name: system-architecture
description: Freeze or review a named host-neutral architecture contract before allocation when a change spans two or more FE, API, BE, or DB layers or changes a shared multi-owner contract. Define boundaries, ownership, lifecycle, failures, safeguards, integration order, and verification without implementing product code.
---

# System Architecture

Use this skill only as the System Architect's primary skill for the named
architecture-contract task. Coding Team remains the sole router: this skill
does not create another runtime, agents, or approval authority.

## Workflow

1. Confirm the trigger and named artifact path in the Lead brief. If fewer than
   two FE/API/BE/DB layers and no shared multi-owner contract are affected,
   stop and route to the smallest accountable role.
2. Read only the named governing references, existing interfaces, relevant
   evidence, human gates, and `core/templates/architecture-contract.md`.
3. Freeze a concise contract covering every template heading. Mark unknowns,
   assumptions, and ownership rather than inventing product requirements.
4. Check the six NFR lenses only when they can change the decision: performance,
   availability/recovery, security/privacy, scalability, maintainability/test,
   and operability/observability. Never invent targets without evidence.
5. For consequential choices, compare only viable options with a compact matrix
   covering fit, correctness/data integrity, security/privacy, operability,
   cost, and migration/reversibility. Record residual risk and the cheapest
   validation experiment.
6. Write or update exactly one named contract/ADR. Do not edit product code,
   allocate builders, integrate work, or issue validation/acceptance decisions.
7. Return the artifact to the Lead. Material implementation drift returns
   **FIO → Lead → System Architect**; builders do not silently revise it.

## Evidence and output

```text
- Label material claims `verified`, `reasoned-not-tested`, or `not-verified`.
- Record planned → actual model capability and any `full`, `reduced`,
  `read-only`, or `planning-only` downshift.
- Return one named contract plus a ≤150-word handoff with evidence labels,
  unresolved gates, residual risk, and next owner.
```

## Coding Team boundaries

- System Architect owns the technical contract; Lead owns cross-role
  synthesis/admission. PM and project-domain roles advise on meaning; they do
  not approve architecture.
- FIO assembles against the frozen contract. The Architect is not FIO and does
  not allocate, integrate, validate, or accept.
- Add Advisor for non-obvious or high-leverage direction. Add Contradictor
  after Advisor for material conflict, shared/public contracts,
  security/privacy, costly reversal, or explicit challenge. Keep debate serial.
- Keep WIP ≤2, disjoint writes, and Test Engineer → Gatekeeper sequential.
- Stop for human approval on production identity, privacy/legal decisions,
  destructive or irreversible migrations, new dependencies/services,
  external providers, deployment, or real personal data.
- Architecture evidence is not Test Engineer evidence or Gatekeeper approval.
