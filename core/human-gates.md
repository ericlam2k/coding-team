# Human gates

Human approval is reserved for decisions that materially change authority,
external state, or reversibility.

## Approval required

- destructive operations or history rewriting;
- production deployment or first public release;
- secrets, credentials, or security-boundary changes;
- new dependencies, services, or permanent infrastructure;
- public-contract breaks, migrations, or material scope expansion;
- commit, push, or merge when the human has not already authorized that action.

## No additional approval required

Inside an authorized scope, the Lead may route roles, implement, correct,
run focused checks, and repeat a failed check after a material fix. A partial
handoff returns to the Lead; it does not create an automatic human gate.

Questions and explanations remain available while a gate is pending. Silence is
never approval. Approval applies only to the named action and scope.
