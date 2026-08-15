# Public repository direction

Status: approved direction; planning only. This document does not approve a
commit, push, merge, tag, public release, or external marketing post.

## Decision

Maintain `coding-team` and WYSY as separate Git repositories.

- `coding-team` remains the public, generic framework.
- WYSY remains the private, unreleased product and private evidence boundary.
- Do not convert `coding-team` into a WYSY branch, subtree, or monorepo path.
- Do not move or rewrite either repository's history.

This follows Git repository boundaries, separation of concerns, and least
privilege. A public framework release cannot inherit private WYSY history,
Customer 0 material, evidence, product policy, or unreleased implementation.

## Current local arrangement

Keep the existing nested `coding-team/` checkout for local development. It is
ignored by the WYSY repository and remains its own Git repository with its own
origin, branches, tags, and release process.

For now, WYSY may resolve the framework through `CODING_TEAM_ROOT` or the
existing repo-local `coding-team/` fallback. Do not add a submodule or subtree.
After the first clean public baseline is released, WYSY should record the
approved semantic version and exact commit SHA it consumes. Upgrade and
rollback then change only that private pin.

## Public starting point

The public story starts from capabilities already present in `coding-team`:

- canonical role cards and explicit ownership;
- Sprint → Batch → Task delivery structure;
- WIP limit of two tool-using specialists;
- human gates for irreversible actions;
- sequential Test Engineer → Gatekeeper review;
- host-neutral core with adapters, installers, templates, and skills.

Candidate features, private WYSY workflows, Customer 0 evidence, experiments,
and unreleased tools must not be described as public, activated, or shipped.

## Next work in `coding-team`

1. Preserve the current dirty worktree; perform no reset or history rewrite.
2. Inventory public-safe, currently available framework capabilities.
3. Prepare the generic pre-Sprint-0 baseline from role cards and the standard
   framework in a clean, disposable public-release checkout.
4. Rewrite the public README with product-marketing language grounded only in
   verified available features.
5. Draft a rolling release agenda: frequent communication, small validated
   increments, and a lower-frequency tagged release cadence.
6. Validate the exact public candidate with an allowlist, private-term and
   secret scans, dependency/license review, Test Engineer evidence,
   Gatekeeper review, and an explicit human release gate.

## Deferred marketing brainstorm

Marketing positioning, Facebook group copy, X copy, audience selection, and
GTM sequencing are intentionally deferred to a separate user-invoked Lead
brainstorm starting from the public `coding-team` repository.

Lead should first frame the audience and decision, then invite the minimum
domain expertise that can change the outcome. Possible instances of the
canonical `domain-advisor` template are `marketing-advisor`,
`social-media-advisor`, or `gtm-advisor`. Do not create a standing panel or
invite all three automatically. Product Manager supplies product value,
Advisor supplies feasibility and leverage, Contradictor challenges the plan,
and Lead synthesizes the final recommendation. No external post is automatic.

## Immediate stop condition

The next session may plan or edit the public `coding-team` documentation. It
must stop before commit, push, merge, tag, release, repository migration, or
external posting unless the user explicitly approves that exact action.
