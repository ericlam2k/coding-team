# Bug fix = root cause

- Fix the cause, not the symptom.
- Grep **callers** of touched functions; fix the shared function once.
- Prefer one shared fix over N call-site patches.
- After fix: one focused check that would have failed before.
- If root cause is outside owned files → stop and escalate with path/line evidence (do not widen ownership silently).
