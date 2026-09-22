---
name: plain-task-start
description: Turn one plain-English request into a short four-line task card (Goal, Scope, Proof, Stop) before any file is changed. Use it to make one small change reviewable; it does not implement, approve, or replace human review.
---

# Plain task start

Use this at the very start of a request, before any file is changed. The card
makes one request small enough to review at a glance. It does not start work,
assign people, or approve anything.

1. **Goal** — restate the request as one everyday sentence: what is different
   when this is done. If the request has two separate outcomes, name the one to
   do first and say the rest waits.
2. **Scope** — list only the files or paths this change may touch. If a path is
   unknown, say `unknown` and ask; never widen the boundary to feel safe.
3. **Proof** — name the one check that shows it works: a command to run, a
   visible result, or a concrete question the change answers. "It compiles" and
   "I reviewed it" are not proof.
4. **Stop** — name the exact moment to pause: right after the proof, and always
   before commit, push, merge, or release.

Reply with the card only, in this format:

```text
Goal: add a dark-mode toggle to the settings page
Scope: src/settings/* only
Proof: toggle switches the preview colors on /settings
Stop: after the preview check, before any commit
```

Then stop and wait. If the request cannot fit one card — two outcomes, no clear
single owner, or a boundary that cannot be named — say so in one line and ask
which part to do first. Do not enlarge the scope to fit the request.
