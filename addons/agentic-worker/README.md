# Agentic Worker addon

Optional app-development overlay for bounded Coding Team Task Specs. It is
default OFF and does not change core routing, roles, model tiers, WIP, human
gates, Test Engineer → Gatekeeper sequencing, or the WYSY platform.

Addon version: `0.1.0` (independent from the Coding Team core version).

Enable explicitly:

```bash
./install.sh --platform codex --global --enable agentic-worker
```

Disable with the matching `--disable agentic-worker` command. Use it only
after Lead has produced a complete Task Spec and frozen scope, interfaces,
invariants, forbidden decisions, and the verification command.

The worker returns the A11 evidence bundle. It does not allocate roles, make
one-way-door decisions, approve work, or replace Test Engineer or Gatekeeper.

This addon is an external extension copied from the supplied skill pack. It is
not source-derived Coding Team core and remains independently removable.

## Rollback

Return immediately to core-only operation:

```bash
./install.sh --platform codex --global --disable agentic-worker
./bin/ct status
```

This removes only the Agentic Worker symlink and leaves the Coding Team core
and QA skill installed. Before installing a future addon version, record its
version and integrated hash in `SOURCE.md`; do not overwrite a pinned version
without a new rollback point.
