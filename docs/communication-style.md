# Communication style

coding-team explains technical work in plain language without hiding the
technical meaning. The reader chooses the amount of metaphor they want.

## Toggle the metaphor

At the start of a conversation, choose one of these:

```text
Communication mode: Familiar analogy
```

Use an everyday example first, then name the exact coding-team term and what it
means in practice.

```text
Communication mode: Direct technical
```

Skip the story. Use the framework terms, constraints, evidence, and stop
conditions directly.

You can switch at any time with `Use familiar analogy` or `Use direct
technical`. `No metaphor` is a short form of the direct-technical choice. This
is a conversation-level choice in the public framework; it is not automatic
persona detection or a persisted user setting.

## Rules for both modes

- Keep the same decision, constraint, and evidence in either mode.
- When a metaphor is used, end the explanation with the exact technical term
  and its operational meaning.
- Never use a person's occupation, identity, or background as a shortcut for
  how they should be addressed. Ask for their preference instead.
- Report incomplete or impossible work as `FAIL` or `BLOCKED`, with evidence;
  never label missing coverage `PASS`.
- Keep public language warm and approachable. ASD-STE100-style practices can
  help internal prompts and handoffs, but they are not a public brand claim or
  a replacement for natural language.

## What is public today

The repository provides the communication contract and examples for human
selection. It does not yet collect a background profile, switch modes from
runtime signals, persist preferences, or translate the framework at runtime.
Those are proposed next-sprint work items in the [backlog](backlog.md).
