# Adapters

The `core/` directory defines host-neutral roles, templates, gates, abstract
tiers, and evidence rules. An adapter binds that policy to a host runtime.

| Adapter | Status | Canonical install |
| --- | --- | --- |
| [Codex](../adapters/codex/) | Supported | `./scripts/install-coding-team.sh --platform codex` |
| [Cursor](../adapters/cursor/) | Supported | `./scripts/install-coding-team.sh --platform cursor` |
| [Cline](../adapters/cline/) | Supported | `./scripts/install-coding-team.sh --platform cline` |

## Shared behavior

Every adapter uses the same Lead → role-card → bounded-task shape, WIP ≤ 2,
disjoint write ownership, Test Engineer → Gatekeeper order, and human gates
for irreversible actions. Only runtime mechanics differ.

## Installation behavior

The canonical installer links the selected adapter and conditional QA support.
It does not refresh or write a model map during setup:

```bash
./scripts/install-coding-team.sh --platform codex
```

The old `--profile hybrid` and `--profile full` spellings are accepted as
compatibility aliases. They install the same payload and are not separate
framework modes.

## Model maps are host-specific

Core tiers describe capability intent; they do not identify a provider or
model. If a host-specific map is useful, inspect the suggestion first:

```bash
./bin/ct map propose --platform codex
```

Write it only after explicit approval:

```bash
./bin/ct map approve --platform codex
```

An approved map belongs to the local host installation. It is not proof that a
concrete slug is available on another host or that the public core is tied to
that provider.
