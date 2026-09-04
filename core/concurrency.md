# Concurrency

Default to no more than two ordinary specialists at once. This is a coordination
preference, not a task-admission ceremony.

## Rules

- One accountable owner per task.
- One writer per file.
- Parallel work requires disjoint writes and no unmet dependency.
- A role that consumes another role's evidence starts after that evidence exists.
- If parallelism adds coordination cost, run the tasks sequentially.
- Specialists do not supervise or control other specialists.

The Lead owns status and routing through handoffs. There is no supervisor lane.

## Common sequencing

- Builder finishes before an independent review of the same bytes.
- Test Engineer runs only when executable behavior needs independent evidence.
- Gatekeeper runs only for material final acceptance or release.
- Advisor and Contradictor run serially when both are genuinely needed.
