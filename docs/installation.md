# Installation

## Quick start: one friendly command

For a normal local setup, use the top-level installer:

```bash
git clone https://github.com/ericlam2k/coding-team.git
cd coding-team
./install.sh
```

The installer detects Codex, Cursor, or Cline when possible. If it finds more
than one host, it asks which one to use. If it cannot detect a host, it offers
Codex as the default. In an interactive session, it can ask for an optional
first project folder.

The project path is used only to add the normal
`coding-team` pointer to that project's `AGENTS.md`. A missing or unwritable
project is reported and skipped; it does not make the framework installation
look successful by silently changing another folder.

Use `--no-questionnaire` for CI or scripts. Combine it with an explicit host
when needed:

```bash
./install.sh --platform codex --no-questionnaire
./install.sh --platform cursor --no-questionnaire
```

The no-questionnaire path never waits for host or communication input. It uses
the safe defaults and does not write a model map. If more than one host is
installed, pass `--platform` to resolve that choice explicitly.

## Advanced: one canonical install

Clone the repository and install the adapter for your host:

```bash
git clone https://github.com/ericlam2k/coding-team.git
cd coding-team
./scripts/install-coding-team.sh --platform codex
```

The same command supports `cursor` and `cline`:

```bash
./scripts/install-coding-team.sh --platform cursor
./scripts/install-coding-team.sh --platform cline
```

The installer links the selected host adapter and conditional QA support. It
does not write a model map, enable addons, or create a second installation
mode. Core policy remains the same on every host.

Use `--check` to inspect an existing activation without changing it:

```bash
./scripts/install-coding-team.sh --check --platform codex
```

Set `CODEX_HOME` to a project-local directory when the host cannot read your
global Codex home. The installer refuses to overwrite a non-symlink target.

## One installation contract

Every public installation command installs the selected host adapter and
conditional QA support. The command does not select an installation variant,
write a model map, or enable an addon. Use the explicit extension commands
below when you need those actions.

## Optional model map

A model map is host-specific configuration, not portable core policy. It is
optional and deliberately separated into a read step and a human-gated write
step:

```bash
# Read-only: show a suggestion and write nothing.
./bin/ct map propose --platform codex

# Explicit approval: prompt, then write the local host map if approved.
./bin/ct map approve --platform codex
```

For a non-interactive environment, `--yes` is an explicit approval signal:

```bash
./bin/ct map approve --platform codex --yes
```

Do not copy a concrete map between hosts. Record the planned tier and actual
host/model choice in the task handoff when the runtime supplies that
information. Missing model telemetry stays unavailable.

## Activate the framework

Set `CODING_TEAM_ROOT` to this checkout and load the adapter skill for your
host. A first task should name one outcome, one boundary, the proof to collect,
and the stop condition.

The shared operating rules are WIP ≤ 2, disjoint writes, Test Engineer →
Gatekeeper sequencing, and a human decision before irreversible actions.

## Conditional QA

| QA path | Public status | Runtime behavior |
|---|---|---|
| **Normal QA** | `AVAILABLE` | Default for ordinary, bounded changes |
| **Risky QA** | `EXPERIMENTAL` | Uses the existing high-risk workflow and evidence rules |

Normal work uses the ordinary focused checks for the task. Risky QA is
implemented and available for careful trial use when a change affects state,
security, privacy, shared contracts, migration/rollback, or has repeated
failures.

Risky or bounded work can load the `qa-evidence-enforcement` skill and its
validator. A bounded pass targets 120 seconds, checkpoints at 180 seconds, and
hard-stops at 240 seconds. A timeout is `BLOCKED` evidence, not an automatic
retry. When a risky trigger applies, do not continue under Normal QA.

`EXPERIMENTAL` is a maturity label, not an enable/disable switch. This update
does not change the installer, trigger policy, validator, or human gates. See
the [basic Risky QA example](examples/risky-qa-trial.md).

## Addons

Addons are separate and default OFF. Enable one only when you need it:

```bash
./bin/ct enable pm-lean
./bin/ct disable pm-lean
```

Addons do not change core routing, role ownership, human gates, or acceptance
authority. See [Addons](addons.md).

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Adapter is not active | Re-run the canonical installer for the selected platform. |
| An installer flag is rejected | Use the documented `--platform`, `--check`, or `--no-questionnaire` command. |
| You want to inspect model choices | Use `./bin/ct map propose`; it is read-only. |
| You want to write a model map | Use `./bin/ct map approve` and make the approval explicit. |
| An addon is not available | Check `./bin/ct status`; addons are opt-in and host-specific. |
