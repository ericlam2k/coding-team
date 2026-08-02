# Integrated QA Operating Model

This is the Coding Team's QA operating layer. Traditional QA supplies the
workflow, layered testing supplies coverage depth, and the bounded evidence
layer controls mutation loops, unclear product meaning, incomplete regression,
and promotion without reliable evidence.

It does not add a router, standing QA meeting, or approval authority. It
preserves WIP ≤2, disjoint write scopes, and sequential Test Engineer (TE) →
Gatekeeper (GK).

## Operating modes

### Standard QA mode

Use the normal QA flow for low-risk, behavior-preserving work. Select only the
test levels and types that the change actually affects. Builders may use
red-green-refactor for local tests; TE still supplies independent batch
evidence when the batch is material.

### Bounded evidence-first mode

Lead activates the overlay for mutation/state, replay or currentness,
ambiguous product/domain meaning, shared contracts, external integrations,
auth/privacy/security, migration/rollback, material regression risk, repeated
failures, or fix–trial behavior. The overlay is a control plane, not a second
test framework.

## Traditional QA flow with owners and gates

| Stage | Accountable owner | Required output / gate |
|---|---|---|
| Requirement analysis | Lead + PM; Domain Advisor and System Architect when triggered | Requirements, user stories, acceptance, risks, dependencies, edge cases, NFR triggers, and unresolved decisions |
| Test planning | TE with Lead | Scope, selected levels/types, environment, entry/exit criteria, owners, evidence plan, regression boundary, and stop condition |
| Test design | TE; PM/domain inputs before freeze | User-observable scenarios, technical invariants, data, negative/exception cases, and requirement traceability; `Frozen for build` or `Draft` with blocked owners |
| Environment setup | Builder/FIO with TE | Build/version, configuration, identities, fixtures, flags, dependencies, logs, monitoring, reset/snapshot, and rollback approach |
| Test execution | TE | Complete required matrix for the frozen Batch, actual results, raw logs, traces, payloads, screenshots, and database/state evidence |
| Defect logging | TE | Scenario reference, severity/priority, repro, expected/actual, evidence, build/data state, suspected layer, and owner |
| Defect triage | Lead | Canonical classification, correlation map, PIC, hypothesis/options, decision, and correction boundary; no patching mid-pass |
| Retesting | TE | Original failure passes on a clean or controlled corrected build; regression case retained |
| Regression | TE | Prior defects, adjacent features, shared components, integrations, workflows, and triggered high-risk paths pass |
| Closure/sign-off | TE → GK → human gate when required | Fresh TE result, open-risk and coverage summary, GK decision, and separate human release/production approval where applicable |

## Layered testing

Layer selection is risk- and change-based. A layer is mandatory when its
trigger applies; no layer is mandatory for every task.

| Layer | Owner | Entry | Exit | Evidence | Mandatory trigger |
|---|---|---|---|---|---|
| **1. Unit** | Builder | Logic and expected behavior are known | Assertions pass; critical local rules covered | Command, assertions, failures, coverage where useful | Changed logic, validation, calculations, mutation guards |
| **2. Component** | Builder; TE support when needed | Unit checks pass; component contract and fixtures exist | Component/API behavior, local persistence, state transitions, and errors match contract | Results, requests/responses, mocks/stubs, local logs | Component, service, local persistence, or local state change |
| **3. Integration** | TE with Builder and System Architect support | Component checks pass; dependency and fixture boundary controlled | Interfaces, mappings, call order, timeout/retry behavior, and dependency failures are correct | Results, logs, traces, payloads, dependency responses | Cross-component, API, database, queue, or external-system change |
| **4. System/E2E** | TE | Integration paths pass; controlled environment is ready | Critical journey works end to end without forbidden leakage or stale state | Run output, screenshots, traces, build/environment ID | Critical user workflow, public contract, auth/privacy, or stateful journey |
| **5. Acceptance/UAT** | PM/domain define; TE executes; human/PIC decides | Product/domain meaning and acceptance are resolved | User outcome, role behavior, customary handling, and recovery expectations are met | Scenario results, domain/product decision, open-risk list | User-facing product behavior, domain meaning, fairness, or material ambiguity |
| **6. Regression** | TE | Integrated change and impact inventory are available | Prior defects, adjacent behavior, shared seams, and high-risk paths pass | Regression matrix, commands, results, gaps | Every non-trivial change; full affected scope for high-risk changes |
| **7. Non-functional** | Relevant specialist with TE | NFR trigger and target are defined | Required performance, reliability, security, privacy, accessibility, or operability evidence passes | Metrics, scans, traces, reports | Only when the change or risk triggers that NFR |

“Test all” means all required scenarios and layers in the frozen Batch before
correction—not the entire repository, every possible layer, or all roles in
parallel.

## Bounded evidence-first overlay

### Plan

Lead opens a bounded concern meeting. PM uses `user-stories` when acceptance
is unclear; PM uses `pre-mortem` when failure, replay, stale-state, or
fix–trial risk is material; a named Domain Advisor supplies domain cases; TE
freezes the scenario matrix; System Architect freezes technical invariants
when the concern crosses boundaries.

### Do

Builders implement one admitted corrective Batch with exclusive files. Local
tests are allowed, but no product fix is dispatched in response to a finding
until the active TE validation pass is complete.

### Check

Fresh TE executes the complete frozen matrix, selected layers, affected
regressions, and relevant negative/adversarial cases. Every finding is logged
and classified as one of:

`PRODUCT_DEFECT`, `TEST_CONTRACT_DEFECT`, `ENVIRONMENT_DEFECT`,
`TOOL_TRANSPORT_DEFECT`, or `UNKNOWN`.

### Act

After collection, correlate all findings once. Cluster only by demonstrated
shared cause; trace to the implementation, product/domain decision, test
contract, or architecture seam. Summarize at most three hypotheses/options and
route to one PIC by default. Use multiple PICs only for distinct technical and
domain decisions. Lead admits one integrable corrective Batch or queues a
separate provisional Batch.

Preserve or add a regression case for every confirmed defect. Run fresh TE
validation after correction, then one sequential GK review. `FAIL`, `BLOCKED`,
stale/insufficient evidence, or GK non-approval stops for the human gate.

## Evidence packet and promotion rule

The final packet must identify the exact build/integration, frozen baseline,
environment/data state, commands and results, defects and classifications,
correlation/root-cause decision, regression result, residual risks, and stop
condition.

Promotion requires fresh TE `PASS` for the same frozen integration and GK
`APPROVE` or `APPROVE_WITH_NOTES`. GK is an evidence gate, not production or
release authority. Human approval remains required for irreversible actions,
production identity/data, privacy/legal decisions, deployment, or other gates
listed in `human-gates.md`.
