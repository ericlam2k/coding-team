# Concurrency

Hard limit: **WIP ≤ 2 ordinary** tool-using worker tasks at once, plus at most
**one read-only supervisor relay lane** when the frozen supervisor-relay
contract is used. The maximum active child lanes is therefore **3**. Lead
(parent) does not count toward ordinary WIP.

## Rules

1. **At most two** concurrent tool-using roles (builders, Investigator, PM, Docs Steward, Advisor, Contradictor, Code Reviewer, Test Engineer, Gatekeeper).
2. For one integrated candidate, the quality chain is strict: mutating Builders stop → candidate is bound and frozen → deterministic checks and complete packet → Code Reviewer risk verification/verdict → Test Engineer when required → Gatekeeper.
3. **Code Reviewer cannot overlap a mutating Builder or Gatekeeper.** It also finishes before Test Engineer starts for that candidate. Candidate mutation invalidates its verdict and restarts the packet/review sequence.
4. **Test Engineer → Gatekeeper is always sequential whenever TE runs.** Never start Gatekeeper until Test Engineer has returned accepted evidence for the same candidate. A direct route is allowed only by `qa-operating-model.md`; Gatekeeper still runs and remains final.
5. **Debate is serial** when Contradictor is required: Investigator (optional) → Advisor → Contradictor → Lead resolution → build. Never run Advisor and Contradictor in parallel. Never run three debate agents at once.
6. **Same-owner exclusive files:** two builders may run in parallel only when owned file sets are disjoint and the brief says so. Overlap → serialize.
7. **Docs Steward** may run in parallel with an unrelated builder only when docs paths do not conflict with builder writes.
8. If a third ordinary tool-using task is needed, **queue it**. Do not start it until an ordinary WIP slot frees.
9. A supervisor lane is non-authoritative observation only: it may read the reserved artifact set and write one create-once relay result. It must not mutate the candidate, control siblings through host APIs, replace TE/Gatekeeper, or supervise another supervisor. No supervisor lane means no extra slot.

## Parallel-safe pairs (examples)

| Pair | OK when |
|---|---|
| Backend + Frontend Builder | Exclusive owned files; no shared contract edit in the same turn |
| Investigator + Docs Steward | Read-only inv + docs-only writes |
| Frontend UX Lead + Investigator | Both read-only / contract-only; no implement |
| Two ordinary workers + supervisor relay | Relay is bounded to its reservation, read-only toward PIC artifacts, and does not advance a quality gate |

## Never parallel

| Pair | Why |
|---|---|
| Test Engineer + Gatekeeper | Evidence must exist before accept/block |
| Code Reviewer + mutating Builder | Reviewer requires an immutable candidate and bound packet |
| Code Reviewer + Test Engineer for the same candidate | Reviewer must decide the evidence route before TE starts |
| Code Reviewer + Gatekeeper | Reviewer verdict is non-terminal; Gatekeeper starts only after the routed evidence is complete |
| Advisor + Contradictor | Debate must be serial |
| Two writers on the same file set | Conflict / merge risk |
| Supervisor + another supervisor | Recursive supervision and duplicate observers create conflicting status authority |
| Supervisor + quality decision | Observation cannot become review, test evidence, acceptance, cancellation policy, or routing authority |
| Gatekeeper + any implementer | Accept only after freeze of evidence |

## Lead duties

- Track active WIP slots in the batch checkpoint.
- Prefer finishing the current pair over starting speculative work.
- On ordinary-WIP pressure: drop lowest-priority queued task or wait — never use the supervisor lane as a third work lane.
