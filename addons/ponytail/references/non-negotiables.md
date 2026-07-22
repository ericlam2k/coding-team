# Not lazy about (non-negotiables)

Ponytail never excuses skipping:

| Area | Requirement |
|---|---|
| Understanding | Read the task and trace the real flow before coding |
| Trust boundaries | Validate at the edge; do not trust client input |
| Data loss | Error handling that prevents silent corruption or wipe |
| Security | Auth, secrets, injection, SSRF, unsafe eval — no shortcuts |
| Accessibility | Interactive UI meets basic a11y for the changed surface |
| Requested work | Explicitly asked scope is not optional |

Non-trivial logic leaves **one runnable check** (test, script, or reproducible command).
