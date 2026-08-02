---
name: system-architecture
description: Review or design system architecture through bounded ADRs, non-functional requirements, technology trade-offs, scalability, and resilience checks. Use for shared contracts, framework or database decisions, migrations, cross-module changes, production-readiness reviews, and architecture conformance audits.
---

# System Architecture Review

Use this skill only as the System Architect's primary skill for a named
architecture concern. Coding Team remains the sole router: this skill does not
create `/flow:*` commands, a backlog runtime, extra agents, or new approval
authority.

## Workflow

1. Read the current architecture baseline, relevant ADRs, product/domain
   contract, role brief, implementation evidence, and human gates before
   proposing a change. Prefer path/line evidence over copied source.
2. State the architecture concern, affected boundaries, constraints, current
   behavior, assumptions, and the smallest reversible decision.
3. Check the six NFR lenses when they can change the decision: performance,
   availability/recovery, security/privacy, scalability, maintainability/test,
   and operability/observability. Mark a lens `not decision-changing` with a
   reason when appropriate; never invent targets without evidence.
4. For technology choices, compare only viable options with a compact weighted
   matrix: product/architecture fit, correctness and data integrity,
   security/privacy, operability, cost, and migration/reversibility. Record
   weights, evidence, residual risk, and the cheapest validation experiment.
5. For a consequential choice, write or update one ADR under `docs/adr/` (or
   the repository's named architecture artifact) with context, decision,
   alternatives, consequences, NFR impact, migration/rollback, and acceptance
   evidence. Inspect related ADRs first and preserve still-valid decisions.
6. Apply scalability and resilience checks only when the concern triggers
   them. Prefer the smallest measured control: timeout, idempotency, bounded
   retry, recovery proof, or a clear manual fallback. Do not introduce CQRS,
   event sourcing, circuit breakers, microservices, queues, or caching merely
   because the pattern is available.
7. Return a contract-ready handoff: decision, owned seams, invariants, API/data
   changes, security/privacy controls, migration risk, test hooks, owner,
   planned→actual model/skill, and stop condition.

## Decision record template

```text
Concern and user/business outcome
Evidence and current behavior
Constraints and assumptions
Options and weighted trade-offs
Decision: Proceed | Modify | Reject | More evidence
NFR impact: performance / availability / security / scalability / maintainability / operability
Data/API/module invariants
Migration, rollback, and residual risk
Cheapest validation experiment
Owner, acceptance artifact, and stop condition
```

## Coding Team boundaries

- System Architect owns the technical contract; Lead owns cross-role
  synthesis/admission. PM and project-domain roles advise on meaning; they do
  not approve architecture.
- Add Advisor for non-obvious or high-leverage direction. Add Contradictor
  after Advisor for material conflict, shared/public contracts,
  security/privacy, costly reversal, or explicit challenge. Keep debate serial.
- Keep WIP ≤2, disjoint writes, and Test Engineer → Gatekeeper sequential.
- Stop for human approval on production identity, privacy/legal decisions,
  destructive or irreversible migrations, new dependencies/services,
  external providers, deployment, or real personal data.
- Architecture evidence is not Test Engineer evidence or Gatekeeper approval.
