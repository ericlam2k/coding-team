---
name: pm-lean-assumption-triage
description: "Explicit-only PM skill for ranking uncertain product assumptions before a human decision. Use when a Product Manager needs to identify the riskiest value, usability, viability, or feasibility beliefs in an unclear proposed change; do not use for routing, implementation, testing, or approval."
---

# PM Lean Assumption Triage

Use only inside the existing Product Manager call. Make no tool, model, role, routing, batch, gate, test, or approval decision. Do not spawn work. Keep the response at or below 250 words.

## Input

Use only the smallest supplied packet:

- proposed outcome or change;
- target user and business context;
- known evidence and constraints; and
- candidate assumptions, if available.

State what is missing instead of inventing facts.

## Method

1. Extract only decision-relevant assumptions.
2. Classify each as Value, Usability, Viability, or Feasibility.
3. Rank by expected impact if wrong and uncertainty, using High/Medium/Low labels; do not imply false precision.
4. Surface missing evidence, dependencies, and an explicit human decision.

Never say or imply "proceed to implementation." This is a decision-support artifact, not admission or execution authority.

## Output

- **Prioritized assumptions:** up to five entries with type, impact, uncertainty, and reason.
- **Missing evidence:** concise list, or `None identified`.
- **Human decision:** choose the single assumption to validate, defer, reject, or reframe; state `Stop — insufficient evidence` when appropriate.
