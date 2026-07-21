# Concurrency

Hard limit: **WIP ≤ 2** tool-using worker tasks at once. Lead (parent) does not count toward WIP.

## Rules

1. **At most two** concurrent tool-using roles (builders, Investigator, PM, Docs Steward, Advisor, Contradictor, Test Engineer, Gatekeeper).
2. **Test Engineer → Gatekeeper is always sequential.** Never start Gatekeeper until Test Engineer has returned accepted evidence for the same batch.
3. **Debate is serial** when Contradictor is required: Investigator (optional) → Advisor → Contradictor → Lead resolution → build. Never run Advisor and Contradictor in parallel. Never run three debate agents at once.
4. **Same-owner exclusive files:** two builders may run in parallel only when owned file sets are disjoint and the brief says so. Overlap → serialize.
5. **Docs Steward** may run in parallel with an unrelated builder only when docs paths do not conflict with builder writes.
6. If a third tool-using task is needed, **queue it**. Do not start it until a WIP slot frees.

## Parallel-safe pairs (examples)

| Pair | OK when |
|---|---|
| Backend + Frontend Builder | Exclusive owned files; no shared contract edit in the same turn |
| Investigator + Docs Steward | Read-only inv + docs-only writes |
| Frontend UX Lead + Investigator | Both read-only / contract-only; no implement |

## Never parallel

| Pair | Why |
|---|---|
| Test Engineer + Gatekeeper | Evidence must exist before accept/block |
| Advisor + Contradictor | Debate must be serial |
| Two writers on the same file set | Conflict / merge risk |
| Gatekeeper + any implementer | Accept only after freeze of evidence |

## Lead duties

- Track active WIP slots in the batch checkpoint.
- Prefer finishing the current pair over starting speculative work.
- On WIP pressure: drop lowest-priority queued task or wait — never raise the limit.
