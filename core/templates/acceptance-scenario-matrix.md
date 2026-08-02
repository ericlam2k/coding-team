# Acceptance Scenario Matrix

## Scope

- Outcome/story:
- Audience/persona:
- Acceptance criteria:
- Contract/constraints:
- Artifact status: `Draft | Frozen for build`
- Owner/date:

## Questions and assumptions

| ID | Question or assumption | Why it matters / affected rows | Smallest owner decision needed | Authorized owner | Status | Resolution evidence or scope effect |
|---|---|---|---|---|---|---|
| Q-01 |  |  |  |  | `Open | Resolved | Deferred` |  |

Do not infer a resolution, deferral, or `N/A`. `Resolved` requires a citation to supplied acceptance/contract text or a named authorized owner decision. `Deferred` requires that owner's decision and the exact scope effect. Any decision-changing unanswered item keeps the artifact `Draft` and affected rows `Blocked`.

## User-observable acceptance scenarios

| ID | User goal/context | Starting state (Given) | Input/action (When) | Expected observable outcome, recovery, and data preservation (Then) | Risk | Automation layer | Status |
|---|---|---|---|---|---|---|---|
| A-01 |  |  |  |  | `Low | Medium | High` | `Unit | Contract | Component | E2E | Manual` | `Ready | Blocked | Deferred` |

Coverage: happy; alternate; mismatch/wrong field; missing/partial/whitespace; nonstandard/multilingual/abbreviated titles; noisy pasted JD; embedded instructions as data; Unicode/malformed/oversized/truncated; duplicate/refresh/back/interruption/recovery; permissions/privacy when relevant. Mark a category `N/A` only when it is demonstrably unreachable from the supplied workflow or contract, and cite that evidence.

## Internal invariants

Keep these separate from user acceptance scenarios.

| ID | Type | Invariant | Verification layer | Status |
|---|---|---|---|---|
| I-01 | `Unit | Security | Concurrency` |  | `Unit | Contract | Integration | Analysis` | `Ready | Blocked | Deferred` |

## Selective TDD map

| Scenario/invariant IDs | Red test target | Green implementation boundary | Refactor guard |
|---|---|---|---|
|  |  |  |  |

Use red-green-refactor for suitable unit, contract, or component cases. Do not force all E2E scenarios to run first.

## Freeze record

- Frozen by/date:
- Resolved/deferred question IDs:
- Acceptance/contract citations and authorized owner decisions:
- Scope changes after freeze:
- Note: `Frozen for build` is a scenario baseline, not execution evidence, Gatekeeper approval, or a completion claim.
