# Product-marketing pack

This pack explains `coding-team` to two audiences at once:

- a newcomer who wants a familiar story before learning framework terms;
- a technical reader who wants the exact role, limit, and evidence language.

## The communication pattern

Use progressive disclosure:

1. Ask what the person already understands.
2. Explain the idea with something from their world.
3. Name the exact framework term.
4. Show the practical choice or next action.
5. Link to the technical policy for readers who want detail.

Example:

> Imagine checking a house before guests arrive. You have the living room,
> bedroom, toilet, and kitchen to check in five minutes. That is too much for
> one reliable check. You can add time, or check fewer rooms first.
>
> In coding-team terms, the Test Engineer has too many acceptance constraints
> for the current timebox. Increase the time budget or reduce/split the
> workload. Do not claim that every check passed.

The story is an explanation of the rule. It is not a promise that the public
installer currently asks for a person’s occupation or automatically chooses a
metaphor.

## User-selected modes

| User choice | First explanation | Exact language after the choice |
|---|---|---|
| Familiar analogy | A daily-life example chosen for the topic | The exact scope, timebox, evidence, and human decision |
| Direct technical | Framework terms, constraints, commands, and failure states | Role cards, acceptance scenarios, WIP ≤ 2, `PASS` / `FAIL` / `BLOCKED` |

See the [communication guide](../communication-style.md) for the copy-paste
mode choices and the [side-by-side validation example](../examples/validation-scenario.md)
for the same scenario in both styles.

## Public/private boundary

The public framework can use this method in README pages, examples, demos, and
social posts. Background-aware onboarding, persona storage, and automatic
communication adaptation are product behavior and must not be advertised as
implemented unless the consuming product has code and tests for them.

ASD-STE100-style writing is useful for agent prompts, handoffs, contracts, and
internal engineering communication: short sentences, active voice, one action
per sentence, and consistent terms. It is not the public brand voice. Public
copy should remain warm and natural while preserving the exact technical terms
after the explanation. Do not claim ASD-STE100 certification.

## Contents

- [Communication guide](../communication-style.md) — choose familiar analogy,
  direct technical, or no metaphor for the conversation.
- [Validation scenario](../examples/validation-scenario.md) — one constraint
  problem explained side by side.
- [Next-sprint backlog](../backlog.md) — proposed adaptation, language,
  marketing, and visual work.

The social drafts, localization editions, and visual case study remain planned
work until they are reviewed and added as complete artifacts.

## Claim boundary

This pack describes capabilities documented in this repository. It does not
describe a private product, hosted dashboard, customer result, model quality,
cost reduction, or unreleased feature. The examples are explanations, not
execution evidence.
