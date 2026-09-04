# QA operating model

QA is proportional to the unresolved risk. It supports the default flow; it is
not a parallel workflow.

## Default

1. The accountable role performs the task.
2. The role runs the focused check named in the Input.
3. The role hands off the result and evidence.
4. The Lead decides whether another quality role has a real question to answer.

## When to use each role

- **Code Reviewer:** independent inspection is valuable for non-trivial code,
  contract, security, or maintainability risk.
- **Test Engineer:** acceptance depends on executable behavior that the
  implementer evidence does not independently prove.
- **Gatekeeper:** material final acceptance, release, migration, security, or
  another explicitly governed decision.

These roles are not mandatory for small deterministic work. When several are
needed, evidence dependencies make them sequential.

## Evidence

Evidence identifies the candidate, focused check, result, defects, and residual
risk. A handoff carries this evidence. Separate QA receipts or validators are
used only when an external audit or release contract explicitly requires them.

Candidate mutation invalidates only evidence affected by the changed bytes or
behavior. Rerun the smallest relevant checks and roles; do not restart an
unrelated full chain.

## Failure route

A failure returns to the Lead. The Lead sends the complete finding set to the
accountable owner, applies the smallest correction, and reruns affected checks.
Ask the human only when the correction changes scope, authority, product meaning,
or an irreversible action.
