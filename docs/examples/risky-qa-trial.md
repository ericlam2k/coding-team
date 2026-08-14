# Basic Risky QA example

Imagine you change who can open a private page in your app.

A normal test checks that the right user can open the page. But this change is
risky because the wrong person could see private information.

Risky QA checks a small, fixed list before anyone says the change is safe:

- the right user can open the page;
- the wrong user is blocked;
- an old saved login does not bypass the new rule;
- an error does not expose private information; and
- the previous behavior can be restored if the change fails.

The team agrees on this list before changing the code. It runs the complete
list, records every result, fixes one bounded problem at a time, and then runs
the list again. Test Engineer checks the evidence before Gatekeeper reviews it.
The human still decides whether to ship.

If the test cannot finish in its time limit, the result is `BLOCKED`, not
`PASS`. The team keeps the evidence and proposes one smaller next task.

Risky QA is currently `EXPERIMENTAL`. The workflow is implemented and
available for careful trial use, while the public guidance is still being
evaluated. This label does not turn safety checks off.
