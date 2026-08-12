# One validation scenario, two explanations

The scenario is identical in both columns. Only the explanation changes.

| Familiar daily-life explanation | Direct technical explanation |
| --- | --- |
| You have four rooms to check before guests arrive: the living room, bedroom, toilet, and kitchen. Each room needs three minutes for a reliable check. | The validation scope contains four areas. Each area requires three minutes of validation. The acceptance constraints are complete coverage and a five-minute total timebox. |
| Four rooms × three minutes = twelve minutes of work. A five-minute timer cannot cover all four rooms properly. | Required validation time is 4 × 3 = 12 minutes, but the timebox is 5 minutes. The constraints are unsatisfiable as written. |
| You can give yourself more time, check fewer rooms, split the rooms into smaller visits, or make the check lighter. | Choose one: increase the timebox; reduce or split the workload; or reduce validation depth. Record the changed acceptance criteria before continuing. |
| If you stop after checking only two rooms, you cannot honestly say the whole house passed. | Partial coverage is not `PASS`. Return `FAIL` when the stated requirement is not met, or `BLOCKED` when the missing time or evidence prevents a valid result. Preserve the evidence and stop condition. |

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
