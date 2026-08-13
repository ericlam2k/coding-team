# One validation scenario

The validation scope contains four areas. Each area requires three minutes of
validation. The acceptance constraints are complete coverage and a five-minute
total timebox.

Required validation time is 4 × 3 = 12 minutes, but the timebox is 5 minutes.
The constraints are unsatisfiable as written.

Choose one: increase the timebox; reduce or split the workload; or reduce
validation depth. Record the changed acceptance criteria before continuing.

Partial coverage is not `PASS`. Return `FAIL` when the stated requirement is
not met, or `BLOCKED` when the missing time or evidence prevents a valid
result. Preserve the evidence and stop condition.

## The framework terms

- **Scope**: what the validation must cover — here, four areas.
- **Timebox**: the maximum time allowed — here, five minutes.
- **Acceptance constraints**: the conditions required for success — here,
  complete coverage at the required depth within the timebox.
- **Evidence**: the observable record of what was checked and what was not.
- **Stop condition**: the point where the team pauses instead of guessing or
  claiming success.

This is an explanation example, not a promise that every installation runs
this exact scenario. The implementation must use the project's actual
acceptance criteria and available evidence.
