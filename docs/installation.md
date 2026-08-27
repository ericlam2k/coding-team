# Install

## Quick start

Clone the public repository and run the friendly installer:

```bash
git clone https://github.com/ericlam2k/coding-team.git
cd coding-team
./install.sh
```

The installer detects Codex, Cursor, or Cline. If it cannot decide, it asks
which host to use. It also asks for an optional project folder. Press Enter to
skip that question.

For scripts or CI, choose the host and skip all questions:

```bash
./install.sh --platform codex --no-questionnaire
```

The installer links the host adapter and QA support. It does not write a model
map or enable an addon.

## Optional project setup

Add the coding-team pointer to a project during install:

```bash
./install.sh --project /path/to/your/project
```

You can do this later:

```bash
./bin/ct project /path/to/your/project
```

## Model map

A model map connects task tiers to models available on your host. It is
optional.

The proposal follows this simple rule:

**Premium decide. Eco build. Cheap search/docs. Human gate for irreversible
risk.**

The proposer reads the host pool and lists every valid model ID. GPT names in
the example map are references, not requirements. If one is unavailable, the
proposer selects a detected model with the closest tier hints. If no useful
hint exists, it uses a fallback and marks the choice as a heuristic. Review the
suggestion before writing it.

Show a proposal without writing a file:

```bash
./bin/ct map propose --platform codex
```

Approve and write the local map:

```bash
./bin/ct map approve --platform codex
```

For automation, --yes is the explicit approval:

```bash
./bin/ct map approve --platform codex --yes
```

Use the same commands with cursor or cline when that host is configured. Do not
copy a map from one host to another.

## Simple safety

Lead checks task size and proof before assigning work. Builders use focused
local checks for low-risk changes. Material or risky work uses Test Engineer →
Gatekeeper, in that order. Run at most two non-conflicting tasks at once.
Human approval is still required for irreversible actions.

## Direct installer

For a host-specific install without the friendly questionnaire:

```bash
./scripts/install-coding-team.sh --platform codex
```

Check an existing install without changing it:

```bash
./scripts/install-coding-team.sh --check --platform codex
```

Set CODEX_HOME when Codex uses a different home directory.

## Optional addon

PM Lean is off by default:

```bash
./bin/ct enable pm-lean
./bin/ct disable pm-lean
```

See [Model-pool mapping](model-pool-mapping.md) for proposal details and
[Project scope](project-scope.md) for the public boundary.
