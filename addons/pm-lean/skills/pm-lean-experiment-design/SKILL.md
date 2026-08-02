---
name: pm-lean-experiment-design
description: "Explicit-only PM skill for designing the smallest safe test for a prioritized product assumption. Use when a Product Manager has an assumption to validate and needs a metric, threshold, and stop criterion; do not use for routing, implementation, testing, or approval."
---

# PM Lean Experiment Design

Use only inside the existing Product Manager call. Make no tool, model, role, routing, batch, gate, test, or approval decision. Do not spawn work. Keep the response at or below 250 words.

## Input

Use only the smallest supplied packet:

- one prioritized assumption;
- target user and decision to inform;
- known evidence, constraints, and available channels; and
- whether a production, destructive, or user-impacting test is proposed.

State what is missing instead of inventing facts.

## Method

1. Prefer the least costly, reversible, and privacy-safe test that can change the decision.
2. Measure observable behavior when possible.
3. Define a measurable threshold before the test.
4. Define a kill or stop criterion and the next human decision.

For production, destructive, or user-impacting experiments, stop at `Human gate required` and name the risk. Do not authorize or execute the experiment.

## Output

- **Assumption:** one sentence.
- **Smallest safe test:** method, audience, scope, and reversible boundary.
- **Metric and threshold:** what is measured and the pass threshold.
- **Kill/stop criterion:** what ends or invalidates the test.
- **Human decision:** validate, revise, stop, or authorize a gated experiment.
