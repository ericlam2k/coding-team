# Project scope

`coding-team` is a standalone public framework for bounded, reviewable
AI-assisted repository work. It is not a mirror of a private application and
does not require access to another product or service.

## What this repository owns

The public repository owns:

- generic role cards and the Sprint → Batch → Task workflow;
- host adapters and installation support;
- bounded evidence rules and human gates;
- communication examples and public-safe demonstrations; and
- documentation needed to use the framework independently.

It does not own product-specific behavior, customer evidence, commercial
release controls, private runtime overlays, provider-specific orchestration,
or an unreviewed product roadmap.

## Separate source projects

Other projects may use this framework internally. A generic artifact from
another checkout may be proposed for this repository only after it is:

1. generalized for users outside its source project;
2. sanitized of private paths, evidence, customer data, and internal handoffs;
3. validated against the public contract; and
4. explicitly approved for the public release.

The repositories keep separate histories, branches, and release decisions.
There is no automatic synchronization in either direction. A public release
does not prove that a related private feature is implemented, activated, or
released.

## Public release checklist

Before a branch is considered for publication, confirm:

- no private implementation, evidence, customer material, or local filesystem
  paths are present;
- the page explains a generic user benefit without private product claims;
- examples and visuals are labelled illustrative unless backed by public
  evidence;
- installer and CLI behavior match the documented public contract; and
- a human has approved the exact staged and published paths.
