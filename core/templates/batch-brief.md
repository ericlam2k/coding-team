# Batch brief

> Cap: **450 words**.

## Identity

- **Batch ID:**
- **Sprint ID:**
- **Title:**
- **Nature (N0–N5 / Consult / Docs):**
- **Planned tier(s):**
- **Scope:** `frontend` | `backend` | `cross-layer` | `ux-contract` | `none`
- **Integration seam:** (one primary seam, or `none`)
- **FIO overlay:** `<canonical role ID> / <task ID>` or `NONE` — exactly one;
  this is an assignment, not a separate role or task
- **FIO status:** `NOT_ASSIGNED` | `IN_PROGRESS` | `READY_FOR_TE` | `DRIFT_REPORTED` | `BLOCKED`
- **Contract ref / hash:** (frozen contract when applicable, otherwise `none`)

## Deliverable

- **Integrated outcome:**
- **Acceptance criteria:**
- **Out of scope:**

## Ownership and exclusive paths

The Batch brief is the source of truth for scope, seam, FIO assignment, and
integration order. Every task has one canonical owner and an exclusive write
set. The FIO may write only its own named paths; it may read named handoffs but
must not patch another owner's paths.

| Role ID / Task ID | Owned files / paths (exclusive) | Notes |
|---|---|---|
| | | |

## Plan

1. Pre-build (Inv / PM / Adv / Con / human gate):
2. Build (parallel rules; one FIO seam check after owners land):
3. FIO handoff (`READY_FOR_TE`, `DRIFT_REPORTED`, or `BLOCKED`):
4. TE evidence:
5. Gatekeeper:
6. Docs (if any):

## Skills to load (explicit)

- (none by default)

## Risks

- **Contract / auth / migration / multi-owner:**
- **Human gate required?** Yes / No — reason:

## Done when

- [ ] TE evidence accepted
- [ ] Gatekeeper decision recorded
