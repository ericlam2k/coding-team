# Architecture contract

> Freeze before Lead allocates builders. One named contract; no product
> implementation or acceptance decision in this artifact.

## Identity

- **Contract ID / status / freeze date:**
- **Trigger:** shared multi-owner contract | 2+ FE/API/BE/DB layers
- **System Architect planned → actual / downshift:**
- **Lead:**
- **FIO after allocation:**

## Scope

- **Outcome and included layers:**
- **Out of scope:**
- **Governing product/domain references:**
- **Human gates required:**

## Contract

| Area | Decision / invariant | Owner after allocation | Evidence label |
|---|---|---|---|
| Boundaries / interfaces | | | verified / reasoned-not-tested / not-verified |
| FE states and user-visible failures | | | |
| API and data ownership / source of truth | | | |
| BE/DB lifecycle, retention, recovery | | | |
| Failure handling and safe degradation | | | |
| Security / privacy / migration / source of truth | | | |
| Observability and operational signals | | | |
| Verification contract | | | |

## Options and decision (when consequential)

- **Viable options considered:**
- **Decision and rationale:**
- **Cost / reversibility / residual risk:**
- **Cheapest validation experiment:**

## Allocation constraints

- **Exclusive writer and file/path boundary per builder:**
- **Integration order and FIO seam checks:**
- **Material drift route:** **FIO → Lead → System Architect**
- **TE → Gatekeeper remains sequential; WIP ≤2:**

## Acceptance boundary

- [ ] Interfaces, ownership, invariants, and failure behavior are stable enough for allocation
- [ ] Evidence labels and model substitution/downshift are recorded
- [ ] Builder, Test Engineer, and Gatekeeper work is not pre-approved by this contract
